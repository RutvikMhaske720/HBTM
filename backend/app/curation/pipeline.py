"""The ingest pipeline: raw candidates in, curated library items out.

A candidate has to clear five gates, cheapest first, so expensive work is
only spent on things still in the running:

1. **Shape** — a real title, a public http(s) link, and a preview image.
2. **Recency** — published inside `curation_max_age_days`. Items whose source
   genuinely has no publication date (books, artworks) are exempt rather than
   silently backdated to now.
3. **Relevance** — a blend of vector similarity against the profile vector and
   lexical overlap with the profile's own words, above
   `curation_relevance_threshold`. This is the gate that enforces "strictly
   relevant to the user profile", and it is applied to *everything*, including
   items that came back from a query the profile itself generated.
4. **Novelty** — not a near-duplicate of anything already in the vector index,
   and not a duplicate of another candidate in this same batch.
5. **Reachability** — the link and the preview image both actually resolve.

Only survivors are written to the library and indexed. Anything rejected is
counted by reason and reported back, so an empty result is explainable rather
than mysterious.
"""

import hashlib
from collections import Counter
from datetime import datetime, timezone

from app.config import get_settings
from app.curation import sources
from app.curation.profile import UserProfile, build_queries
from app.db.database import Store
from app.db.models import new_content_item
from app.embeddings import index
from app.embeddings.embedder import get_embedder
from app.mcp_tools import semantic_search, web_search

# Media where "recent" is the wrong axis. A book's publication year and the
# date Openverse happened to index an artwork say nothing about whether the
# work is worth reading or looking at now, and cutting on them throws away
# exactly the durable material these shelves exist for. Freshness is still
# pursued for them at the source (Open Library is queried newest-first); it
# just isn't a rejection criterion.
_TIMELESS_SOURCES = {"openlibrary", "openverse", "pinterest"}

# Titles that are engagement bait regardless of topic. The Safety Agent scores
# these too; catching them here keeps them out of the library entirely.
_BAIT_MARKERS = (
    "you won't believe", "shocking", "one weird trick", "gurus hide",
    "doctors hate", "get rich quick", "!!!", "100% guaranteed",
)


def _stable_id(source: str, external_id: str) -> str:
    return f"ext-{hashlib.sha1(f'{source}-{external_id}'.encode()).hexdigest()[:12]}"


def _candidate_text(candidate: dict) -> str:
    return f"{candidate.get('title','')} {candidate.get('description','')}".strip()


def _normalized_date(published_at: str) -> str:
    """Store one date format, whatever a source hands us.

    Sources differ: YouTube emits a trailing "Z", feeds emit RFC 2822, Open
    Library emits a bare year. Normalising once here means every consumer
    downstream — ranking, the recency gate, the API layer — can assume an
    ISO-8601 string with an offset.
    """
    return web_search.parse_date(published_at)


def _age_days(published_at: str, now: datetime) -> float | None:
    normalized = _normalized_date(published_at)
    if not normalized:
        return None
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return max((now - parsed).total_seconds() / 86400, 0.0)


def _lexical_overlap(text: str, terms: set[str]) -> float:
    """Fraction of the profile's own words the candidate actually mentions."""
    if not terms:
        return 0.0
    words = {word for word in text.lower().split() if len(word) > 3}
    if not words:
        return 0.0
    hits = sum(1 for term in terms if term in words)
    return min(hits / min(len(terms), 8), 1.0)


# A cosine of 0.15 does not mean the same thing for every source, because the
# amount of text available to compare differs by an order of magnitude. A
# YouTube item carries a title plus a description of up to 1000 characters; an
# Openverse record carries a title and a handful of tags; an iTunes show
# carries "artist · genre · episode count". Scoring them all against one cut
# does not enforce a consistent standard, it just rejects whichever sources
# happen to be terse. These scales were set from measured score distributions
# per source, choosing the point that separated on-topic from off-topic
# results for each: e.g. for podcasts it keeps "Deep Questions with Cal
# Newport" for a deep-reading goal while dropping an Instagram marketing show.
_SOURCE_THRESHOLD_SCALE = {
    "youtube": 1.00,     # title + long description
    "spotify": 1.00,     # title + artist + album
    "web": 1.00,         # title + Open Graph description
    "openlibrary": 0.80,  # author + year + subject headings
    "pinterest": 0.80,   # title + user-written description
    "itunes": 0.72,      # artist + genre + episode count
    "openverse": 0.68,   # title + machine-generated tags
}


def threshold_for(source: str, base: float) -> float:
    return base * _SOURCE_THRESHOLD_SCALE.get(source, 1.0)


def relevance(
    candidate_vector: list[float], text: str, profile: UserProfile,
    intent_vector: list[float], terms: set[str],
) -> float:
    """How well a candidate matches this user, in [0, 1].

    Three signals, because no single one is sufficient:

    * **intent** — similarity to the queries that fetched it. These queries
      were themselves generated from the profile, so this stays a measure of
      profile fit; it just measures it where the vocabulary actually meets.
      Without it, "ambient study music for long reading sessions" scores near
      zero against a reading goal stated in completely different words, and
      every legitimately-relevant Music result gets thrown away.
    * **profile** — direct similarity to the identity-and-goals text, which
      is what catches a result that matched the query wording but drifted off
      the person.
    * **lexical** — a floor of literal overlap, so an item that names the
      user's actual goal can't be rejected on vector geometry alone.
    """
    embedder = get_embedder()
    if not profile.vector and not intent_vector:
        return 1.0  # anonymous browse — there is no profile to be relevant to
    intent = embedder.similarity(candidate_vector, intent_vector) if intent_vector else 0.0
    personal = embedder.similarity(candidate_vector, profile.vector) if profile.vector else 0.0
    return max(0.0, 0.50 * intent + 0.30 * personal + 0.20 * _lexical_overlap(text, terms))


def curate(
    db: Store,
    profile: UserProfile,
    content_type: str,
    domain: str | None = None,
    limit: int | None = None,
) -> tuple[list[dict], dict]:
    """Fetch, filter and persist fresh items for one medium.

    Returns `(items, report)`. `report` counts what was rejected and why.
    """
    settings = get_settings()
    limit = limit or settings.curation_target_per_type
    resolved_domain = domain or profile.domains[0]
    now = datetime.now(timezone.utc)
    rejected: Counter = Counter()

    # The queries are both what gets sent to the sources and what results are
    # scored against, so relevance is measured against the same intent that
    # produced the candidate rather than against unrelated profile wording.
    queries = build_queries(profile, content_type, resolved_domain)
    intent_vector = semantic_search.embed_text(" ".join(queries))
    terms = profile.terms | {
        word for query in queries for word in query.lower().split() if len(word) > 3
    }

    candidates = sources.collect(profile, content_type, resolved_domain, queries=queries)
    rejected["fetched"] = len(candidates)

    # ── Gate 1: shape ──────────────────────────────────────────────────────
    shaped = []
    for candidate in candidates:
        title = (candidate.get("title") or "").strip()
        url = candidate.get("url", "")
        thumbnail = candidate.get("thumbnail_url", "")
        if len(title) < 3 or any(marker in title.lower() for marker in _BAIT_MARKERS):
            rejected["unusable_title"] += 1
        elif not web_search.is_public_http_url(url):
            rejected["bad_link"] += 1
        elif not web_search.is_public_http_url(thumbnail):
            rejected["no_preview"] += 1
        else:
            shaped.append(candidate)

    # ── Gate 2: recency ────────────────────────────────────────────────────
    recent = []
    for candidate in shaped:
        if candidate["source"] in _TIMELESS_SOURCES:
            recent.append(candidate)
            continue
        age = _age_days(candidate.get("published_at", ""), now)
        if age is None:
            rejected["undated"] += 1
        elif age <= settings.curation_max_age_days:
            recent.append(candidate)
        else:
            rejected["stale"] += 1

    if not recent:
        return [], {"content_type": content_type, "domain": resolved_domain, "kept": 0, **rejected}

    # ── Gate 3: relevance to this profile ──────────────────────────────────
    texts = [_candidate_text(candidate) for candidate in recent]
    vectors = semantic_search.embed_many(texts)
    scored = []
    for candidate, text, vector in zip(recent, texts, vectors):
        score = relevance(vector, text, profile, intent_vector, terms)
        if score < threshold_for(candidate["source"], settings.curation_relevance_threshold):
            rejected["irrelevant"] += 1
            continue
        scored.append((score, candidate, vector))
    scored.sort(key=lambda entry: entry[0], reverse=True)

    # ── Gate 4: novelty, against the index and within this batch ───────────
    selected: list[tuple[float, dict, list[float]]] = []
    for score, candidate, vector in scored:
        content_id = _stable_id(candidate["source"], candidate["external_id"])
        if db.content_items.get(content_id):
            # Already curated — refresh it in place rather than re-adding.
            rejected["already_known"] += 1
            continue
        near = semantic_search.find_duplicates(vector, settings.curation_duplicate_threshold)
        if near:
            rejected["duplicate"] += 1
            continue
        if any(
            get_embedder().similarity(vector, chosen_vector) >= settings.curation_duplicate_threshold
            for _, _, chosen_vector in selected
        ):
            rejected["duplicate"] += 1
            continue
        selected.append((score, candidate, vector))
        if len(selected) >= limit:
            break

    # ── Gate 5: the link and the preview are not dead ──────────────────────
    if settings.curation_verify_links and selected:
        checks = web_search.check_urls(
            [candidate["url"] for _, candidate, _ in selected]
            + [candidate["thumbnail_url"] for _, candidate, _ in selected]
        )
        alive = []
        for entry in selected:
            _, candidate, _ = entry
            states = (checks.get(candidate["url"]), checks.get(candidate["thumbnail_url"]))
            if "dead" in states:
                rejected["dead_link"] += 1
            else:
                alive.append(entry)
        selected = alive

    items = [
        _to_record(candidate, content_type, resolved_domain, score, profile.user_id)
        for score, candidate, _ in selected
    ]
    for item in items:
        db.content_items.upsert(item)
    index.index_items(db, items)

    report = {
        "content_type": content_type,
        "domain": resolved_domain,
        "kept": len(items),
        **{reason: count for reason, count in rejected.items()},
    }
    return items, report


def _to_record(candidate: dict, content_type: str, domain: str, score: float, user_id: str = "") -> dict:
    """Turn a surviving candidate into a library record.

    `growth_potential_score` is anchored to how well the item matched this
    profile, so an item that barely cleared the relevance gate doesn't then
    outrank a strong match on the strength of a hardcoded default.
    `relevance_score` keeps the raw figure as provenance — it is the record
    that this item passed the gates rather than predating them.
    """
    return new_content_item(
        id=_stable_id(candidate["source"], candidate["external_id"]),
        title=candidate["title"],
        content_type=content_type,
        domain=domain,
        description=candidate["description"],
        growth_potential_score=round(min(0.95, 0.45 + score * 0.5), 3),
        difficulty="accessible",
        duration_minutes=candidate.get("duration_minutes", 10),
        mood="curious",
        source=candidate["source"],
        url=candidate["url"],
        thumbnail_url=candidate["thumbnail_url"],
        video_id=candidate.get("video_id", ""),
        published_at=(
            _normalized_date(candidate.get("published_at", ""))
            or datetime.now(timezone.utc).isoformat()
        ),
        relevance_score=round(score, 4),
        curated_for=user_id,
    )


def curate_many(
    db: Store, profile: UserProfile, content_type: str, domains: list[str] | None = None,
    limit_per_domain: int | None = None,
) -> tuple[list[dict], list[dict]]:
    """Curate one medium across several of the user's goal domains."""
    items, reports = [], []
    for domain in (domains or profile.domains)[:3]:
        curated, report = curate(db, profile, content_type, domain, limit_per_domain)
        items.extend(curated)
        reports.append(report)
    return items, reports
