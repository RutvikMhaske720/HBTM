"""Library maintenance at startup.

There is deliberately no seed catalogue any more. The previous one was
invented content — plausible titles and descriptions with no source URL and
no preview image behind them. Under the curator's current rules those items
are unservable by definition: nothing without a working link and a real
preview reaches a user, so a synthetic catalogue could only ever be dead
weight in the ranking and dead buttons in the UI.

The library is now built entirely from live sources (`app.curation`), on
demand and per profile. What remains here is the housekeeping that has to run
before anything is served:

* migrate records written under older content-type names;
* drop legacy rows that can never be shown;
* fit the embedder and rebuild the vector index (see `app.embeddings.index`).
"""

from app.db.database import Store
from app.embeddings.index import ensure_index
from app.mcp_tools.web_search import is_public_http_url, parse_date

# Old name -> current name. "Film" became "Videos" because the medium being
# curated is short-form video, not cinema.
CONTENT_TYPE_RENAMES = {"Film": "Videos", "Video": "Videos"}

# What each source is actually capable of producing, and what to relabel an
# item as when it claims something else. Earlier ingestion fell back to
# YouTube for every medium, which left videos filed under "Print" and "Art" —
# a real link and a real preview, but the wrong shelf.
SOURCE_TYPES = {
    "youtube": ({"Videos", "Animation", "Music"}, "Videos"),
    "spotify": ({"Music"}, "Music"),
    "openverse": ({"Art"}, "Art"),
    "pinterest": ({"Art"}, "Art"),
    "openlibrary": ({"Print"}, "Print"),
    "itunes": ({"Podcast"}, "Podcast"),
    "web": ({"Editorial", "Print"}, "Editorial"),
}


def migrate_content_types(db: Store) -> int:
    """Rewrite records using a retired name or a type their source can't produce."""
    migrated = 0
    for item in db.content_items.all():
        current = item.get("content_type", "")
        target = CONTENT_TYPE_RENAMES.get(current, current)
        allowed, fallback = SOURCE_TYPES.get(item.get("source", ""), (set(), ""))
        if allowed and target not in allowed:
            target = fallback
        if target != current:
            item["content_type"] = target
            db.content_items.upsert(item)
            migrated += 1
    return migrated


def normalize_dates(db: Store) -> int:
    """Rewrite stored dates into one parseable ISO-8601 form.

    Records ingested before normalisation kept whatever their source emitted,
    including YouTube's trailing "Z" — which `datetime.fromisoformat` rejects
    before Python 3.11. A single such record used to abort scoring for the
    entire batch, so these are repaired rather than tolerated.
    """
    fixed = 0
    for item in db.content_items.all():
        raw = item.get("published_at", "")
        normalized = parse_date(raw)
        if normalized and normalized != raw:
            item["published_at"] = normalized
            db.content_items.upsert(item)
            fixed += 1
    return fixed


def prune_unservable(db: Store) -> int:
    """Delete library rows that can't be shown, or were never vetted.

    Two kinds of row go:

    * **Unrenderable** — no usable link, or no preview. Records from the
      retired synthetic catalogue, plus anything whose source stopped serving
      an image. These can never be displayed, so keeping them only distorts
      ranking.
    * **Ungated** — no `relevance_score`, meaning the row was ingested before
      the curation gates existed. Earlier ingestion built queries by pasting a
      goal title next to a media type, so a Print request for "Finish one
      long-form resource a month" returned "Free Print Portal for Cyber Cafe".
      Those rows have working links and real thumbnails, so no display check
      catches them — but they were never matched to anybody's profile, and
      leaving them in means recommendations lead with them.
    """
    removed = 0
    for item in db.content_items.all():
        has_link = is_public_http_url(item.get("url", ""))
        has_preview = bool(item.get("video_id")) or is_public_http_url(item.get("thumbnail_url", ""))
        vetted = item.get("relevance_score") is not None
        if not (has_link and has_preview and vetted):
            db.content_items.delete(item["id"])
            removed += 1
    return removed


def prepare_library(db: Store) -> dict:
    """Run every startup maintenance step and report what changed."""
    migrated = migrate_content_types(db)
    redated = normalize_dates(db)
    removed = prune_unservable(db)
    # Pruning changes the corpus, so the index is rebuilt after it, not before.
    index_report = ensure_index(db, force=bool(removed or migrated))
    return {"migrated": migrated, "redated": redated, "pruned": removed, **index_report}
