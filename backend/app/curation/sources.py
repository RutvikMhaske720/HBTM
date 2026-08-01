"""Source adapters, one per real provider, all returning the same shape.

Every adapter returns a list of *candidates*:

    {source, external_id, title, description, url, thumbnail_url,
     video_id, duration_minutes, published_at}

`url` and `thumbnail_url` are mandatory and must already be real — an adapter
that cannot produce both for an item drops it rather than emitting a
placeholder. The pipeline re-checks this, but keeping the rule at the source
means a broken record never travels far enough to be reasoned about.

Which adapters run for a given medium is decided by `adapters_for`. Music runs
Spotify *and* YouTube because the two catalogues barely overlap for this
purpose: Spotify has the tracks, YouTube has the mixes, live sets and hour-long
focus sessions people actually put on while working.
"""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from app.config import get_settings
from app.curation.profile import (
    DOMAIN_FEEDS,
    DOMAIN_SEARCH_SITES,
    PRINT_SUBJECTS,
    UserProfile,
    build_queries,
)
from app.mcp_tools import open_library, openverse, pinterest, podcasts, spotify, web_search, youtube

Candidate = dict


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Video-backed adapters ─────────────────────────────────────────────────────

def _from_youtube(videos: list[dict]) -> list[Candidate]:
    return [
        {
            "source": "youtube",
            "external_id": video["video_id"],
            "title": video["title"],
            "description": (video["description"] or f"From {video['channel']} on YouTube.")[:1000],
            "url": video["url"],
            "thumbnail_url": video["thumbnail_url"],
            "video_id": video["video_id"],
            "duration_minutes": max(1, video["duration_seconds"] // 60),
            "published_at": video["published_at"],
        }
        for video in videos
        if video.get("thumbnail_url") and video.get("url")
    ]


def videos(query: str, domain: str, limit: int) -> list[Candidate]:
    settings = get_settings()
    return _from_youtube(youtube.search_youtube_videos(
        query=query, category=domain, max_results=limit,
        published_within_days=settings.curation_max_age_days,
        video_category_id=youtube.CATEGORY_EDUCATION,
    ))


def animation(query: str, domain: str, limit: int) -> list[Candidate]:
    settings = get_settings()
    return _from_youtube(youtube.search_youtube_videos(
        query=query, category=domain, max_results=limit,
        published_within_days=settings.curation_max_age_days,
        video_category_id=youtube.CATEGORY_FILM_ANIMATION,
    ))


def music_youtube(query: str, domain: str, limit: int) -> list[Candidate]:
    """YouTube's music category — mixes and long focus sessions Spotify lacks."""
    settings = get_settings()
    return _from_youtube(youtube.search_youtube_videos(
        query=query, category=domain, max_results=limit,
        published_within_days=settings.curation_max_age_days,
        video_category_id=youtube.CATEGORY_MUSIC,
    ))


def music_spotify(query: str, domain: str, limit: int) -> list[Candidate]:
    settings = get_settings()
    if not settings.spotify_configured:
        return []
    try:
        tracks = spotify.search_tracks(query=query, max_results=limit)
    except Exception:
        # Spotify's client-credentials flow fails for app/account policy
        # reasons that have nothing to do with this query; YouTube covers it.
        return []
    return [
        {
            "source": "spotify",
            "external_id": track["track_id"],
            "title": track["title"],
            "description": track["description"],
            "url": track["url"],
            "thumbnail_url": track["thumbnail_url"],
            "video_id": "",
            "duration_minutes": max(1, track["duration_seconds"] // 60),
            "published_at": track["published_at"],
        }
        for track in tracks
        if track.get("thumbnail_url") and track.get("url")
    ]


# ─── Web-scraped and open-API adapters ─────────────────────────────────────────

def art(query: str, domain: str, limit: int) -> list[Candidate]:
    settings = get_settings()
    candidates: list[Candidate] = []
    if settings.pinterest_configured:
        try:
            candidates += [
                {
                    "source": "pinterest",
                    "external_id": pin["pin_id"],
                    "title": pin["title"],
                    "description": pin["description"],
                    "url": pin["url"],
                    "thumbnail_url": pin["image_url"],
                    "video_id": "",
                    "duration_minutes": 3,
                    "published_at": pin["published_at"],
                }
                for pin in pinterest.get_board_pins(limit=limit)
                if pin.get("image_url")
            ]
        except Exception:
            candidates = []
    candidates += [
        {
            "source": "openverse",
            "external_id": image["image_id"],
            "title": image["title"],
            "description": image["description"],
            "url": image["url"],
            "thumbnail_url": image["thumbnail_url"],
            "video_id": "",
            "duration_minutes": 3,
            "published_at": image["published_at"],
        }
        for image in openverse.search_images(query, max_results=limit)
    ]
    return candidates


def print_media(query: str, domain: str, limit: int) -> list[Candidate]:
    return [
        {
            "source": "openlibrary",
            "external_id": book["work_id"],
            "title": book["title"],
            "description": book["description"],
            "url": book["url"],
            "thumbnail_url": book["thumbnail_url"],
            "video_id": "",
            "duration_minutes": 240,  # a book is a commitment, not a sitting
            "published_at": book["published_at"] or _now(),
        }
        for book in open_library.search_books(
            query, max_results=limit, subject=PRINT_SUBJECTS.get(domain, "")
        )
    ]


def podcast(query: str, domain: str, limit: int) -> list[Candidate]:
    return [
        {
            "source": "itunes",
            "external_id": show["show_id"],
            "title": show["title"],
            "description": show["description"],
            "url": show["url"],
            "thumbnail_url": show["thumbnail_url"],
            "video_id": "",
            "duration_minutes": 45,
            "published_at": show["published_at"],
        }
        for show in podcasts.search_podcasts(query, max_results=limit)
    ]


def editorial(query: str, domain: str, limit: int) -> list[Candidate]:
    """Scrape the open web for writing, then verify every lead has a preview.

    Three channels, because no single one is dependable:

    * a configured search provider or DuckDuckGo — best when available, but
      keyless engines captcha-gate automated traffic on many networks;
    * **publisher search feeds** — each curated publication queried directly
      through its own RSS search, which needs no key and is not gated. This
      is what makes results track the query rather than the calendar;
    * plain publisher feeds — the freshness floor.

    Search results and feed entries are only URLs. `extract_previews` fetches
    each page and reads its Open Graph tags, which simultaneously proves the
    link resolves and yields the image and canonical URL used downstream.
    """
    published_by_url: dict[str, str] = {}
    leads = web_search.web_search(query, max_results=limit * 2, recency_days=365)

    searched = web_search.search_site_feeds(
        DOMAIN_SEARCH_SITES.get(domain, []), query, limit_per_site=6
    )
    for entry in searched + web_search.fetch_feeds(DOMAIN_FEEDS.get(domain, []), limit_per_feed=6):
        published_by_url.setdefault(entry["url"], entry["published_at"])
        leads.append(entry)

    urls = list(dict.fromkeys(lead["url"] for lead in leads))[: limit * 5]
    snippets = {lead["url"]: lead.get("snippet", "") for lead in leads}

    candidates = []
    for preview in web_search.extract_previews(urls):
        source_url = preview["url"]
        description = (
            preview["description"]
            or snippets.get(preview["lead_url"], "")
            or snippets.get(source_url, "")
        )
        candidates.append({
            "source": "web",
            "external_id": source_url,
            "title": preview["title"] or preview["site_name"],
            "description": (description or f"Published by {preview['site_name']}.")[:1000],
            "url": source_url,
            "thumbnail_url": preview["thumbnail_url"],
            "video_id": "",
            "duration_minutes": 8,
            "published_at": (
                preview["published_at"]
                or published_by_url.get(preview["lead_url"], "")
                or published_by_url.get(source_url, "")
                or _now()
            ),
            "site_name": preview["site_name"],
        })
    return candidates


# ─── Routing ───────────────────────────────────────────────────────────────────

Adapter = Callable[[str, str, int], list[Candidate]]

_ADAPTERS: dict[str, list[Adapter]] = {
    "Videos": [videos],
    "Music": [music_spotify, music_youtube],
    "Animation": [animation],
    "Art": [art],
    "Print": [print_media],
    "Podcast": [podcast],
    "Editorial": [editorial],
}


def adapters_for(content_type: str) -> list[Adapter]:
    """Adapters for a medium; unknown media fall back to open-web scraping."""
    return _ADAPTERS.get(content_type, [editorial])


def supported_types() -> list[str]:
    return list(_ADAPTERS)


def collect(
    profile: UserProfile, content_type: str, domain: str,
    per_query: int = 6, queries: list[str] | None = None,
) -> list[Candidate]:
    """Run every adapter for this medium across every profile-derived query.

    Adapters are independent network calls, so they run concurrently; the
    whole fan-out costs about as long as its slowest single request.
    """
    settings = get_settings()
    queries = queries or build_queries(profile, content_type, domain)
    jobs = [
        (adapter, query)
        for adapter in adapters_for(content_type)
        for query in queries
    ]
    if not jobs:
        return []

    def run(job: tuple[Adapter, str]) -> list[Candidate]:
        adapter, query = job
        try:
            return adapter(query, domain, per_query)
        except Exception:
            # One dead provider must not take down the whole fan-out.
            return []

    with ThreadPoolExecutor(max_workers=min(settings.curation_max_workers, len(jobs))) as pool:
        batches = list(pool.map(run, jobs))

    merged: dict[str, Candidate] = {}
    for batch in batches:
        for candidate in batch:
            key = f"{candidate['source']}:{candidate['external_id']}"
            merged.setdefault(key, candidate)
    return list(merged.values())
