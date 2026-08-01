"""MCP: Openverse image search — the source behind curated Art.

Openverse indexes openly-licensed images from museums, archives and photo
libraries, and needs no API key. Every record carries both a hosted thumbnail
and a `foreign_landing_url` pointing at the work on its original site, which
is exactly the link + preview pair the curator requires.

Pinterest (see `pinterest.py`) stays the preferred Art source when an account
is connected, because it reflects a board the user actually curated; this is
what runs otherwise.
"""

from datetime import datetime, timezone

import httpx

from app.config import get_settings
from app.mcp_tools.web_search import USER_AGENT, is_public_http_url

API_URL = "https://api.openverse.org/v1/images/"


def search_images(query: str, max_results: int = 10) -> list[dict]:
    settings = get_settings()
    try:
        response = httpx.get(
            API_URL,
            params={
                "q": query,
                "page_size": min(max(max_results, 1), 20),
                "mature": "false",
                # Only licences that permit showing the work in a feed.
                "license_type": "all-cc",
            },
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=settings.curation_http_timeout,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return []

    images = []
    for item in response.json().get("results", []):
        landing = item.get("foreign_landing_url") or item.get("url") or ""
        thumbnail = item.get("thumbnail") or item.get("url") or ""
        if not (is_public_http_url(landing) and is_public_http_url(thumbnail)):
            continue
        creator = item.get("creator") or "Unknown artist"
        source = item.get("source") or "Openverse"
        # Tags are the only text that describes what is actually *in* the
        # image. Without them a record reads "creator · source · licence",
        # which tells a relevance check nothing about the subject matter.
        tags = ", ".join(
            tag["name"] for tag in item.get("tags", [])
            if isinstance(tag, dict) and tag.get("name")
        )[:300]
        images.append({
            "image_id": str(item.get("id", "")),
            "title": (item.get("title") or "Untitled work").strip()[:300],
            "description": " · ".join(part for part in [
                tags, creator, source,
                item["license"].upper() if item.get("license") else "",
            ] if part),
            "thumbnail_url": thumbnail,
            "url": landing,
            "published_at": _indexed_at(item),
        })
    return [image for image in images if image["image_id"]]


def _indexed_at(item: dict) -> str:
    """Openverse reports when it indexed a work, not when the work was made."""
    raw = item.get("indexed_on") or ""
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
    except ValueError:
        return datetime.now(timezone.utc).isoformat()
