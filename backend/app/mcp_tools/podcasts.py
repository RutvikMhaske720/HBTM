"""MCP: iTunes Search — the source behind curated Podcast items.

Keyless. Apple returns high-resolution artwork and a public podcast page for
every hit, and `releaseDate` reflects the most recent episode, which is what
makes the recency gate meaningful for a long-running show.
"""

from datetime import datetime, timezone

import httpx

from app.config import get_settings
from app.mcp_tools.web_search import USER_AGENT, parse_date, is_public_http_url

SEARCH_URL = "https://itunes.apple.com/search"


def search_podcasts(query: str, max_results: int = 10) -> list[dict]:
    settings = get_settings()
    try:
        response = httpx.get(
            SEARCH_URL,
            params={
                "term": query,
                "media": "podcast",
                "entity": "podcast",
                "limit": min(max(max_results, 1), 25),
                "explicit": "No",
            },
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=settings.curation_http_timeout,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return []

    shows = []
    for item in response.json().get("results", []):
        artwork = item.get("artworkUrl600") or item.get("artworkUrl100") or ""
        landing = item.get("collectionViewUrl") or item.get("trackViewUrl") or ""
        collection_id = item.get("collectionId")
        if not collection_id or not (is_public_http_url(artwork) and is_public_http_url(landing)):
            continue
        genres = ", ".join(item.get("genres", [])[:3])
        episodes = item.get("trackCount")
        shows.append({
            "show_id": str(collection_id),
            "title": (item.get("collectionName") or "Untitled podcast").strip()[:300],
            "description": " · ".join(part for part in [
                item.get("artistName", ""),
                genres,
                f"{episodes} episodes" if episodes else "",
            ] if part)[:500],
            "thumbnail_url": artwork,
            "url": landing,
            "feed_url": item.get("feedUrl", ""),
            "published_at": parse_date(item.get("releaseDate")) or datetime.now(timezone.utc).isoformat(),
        })
    return shows
