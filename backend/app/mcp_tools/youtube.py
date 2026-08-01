"""MCP: YouTube Data API integration (spec section 8.2.1).

Every result this module returns is a real, embeddable, currently-available
video with a real thumbnail. Anything that fails those checks is dropped here
rather than being passed downstream to be filtered later — a video that can't
be embedded has no preview, and an unavailable one is a broken link.
"""

import re
from datetime import datetime, timedelta, timezone

import httpx

from app.config import get_settings

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

# YouTube's own topic buckets. Constraining the search to one keeps a "Music"
# request from returning a lecture *about* music, and an "Animation" request
# from returning live-action.
CATEGORY_MUSIC = "10"
CATEGORY_FILM_ANIMATION = "1"
CATEGORY_EDUCATION = "27"

_DURATION_PATTERN = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


def search_youtube_videos(
    query: str,
    category: str | None = None,
    max_results: int = 5,
    safe_search: bool = True,
    published_within_days: int | None = None,
    video_category_id: str | None = None,
    order: str = "relevance",
) -> list[dict]:
    """Search YouTube and return only playable, previewable videos.

    `order="date"` gives the newest matches but sacrifices relevance, so
    callers that care about both pass `order="relevance"` together with
    `published_within_days` — that way the recency constraint is applied by
    the API as a filter, and ranking stays relevance-driven.
    """
    settings = get_settings()
    if not settings.youtube_configured:
        return []

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": min(max(max_results, 1), 50),
        "order": order,
        "safeSearch": "strict" if safe_search else "none",
        "videoEmbeddable": "true",
        "relevanceLanguage": "en",
        "key": settings.youtube_api_key,
    }
    if video_category_id:
        params["videoCategoryId"] = video_category_id
    if published_within_days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=published_within_days)
        params["publishedAfter"] = cutoff.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    try:
        with httpx.Client(timeout=settings.curation_http_timeout + 5) as client:
            response = client.get(SEARCH_URL, params=params)
            response.raise_for_status()
            ids = [
                item.get("id", {}).get("videoId")
                for item in response.json().get("items", [])
            ]
            ids = [video_id for video_id in ids if video_id]
            if not ids:
                return []
            details = client.get(
                VIDEOS_URL,
                params={
                    "part": "snippet,contentDetails,status",
                    "id": ",".join(ids),
                    "key": settings.youtube_api_key,
                },
            )
            details.raise_for_status()
    except httpx.HTTPError:
        return []

    details_by_id = {item["id"]: item for item in details.json().get("items", [])}
    results = []
    for video_id in ids:  # preserve the API's ranking
        item = details_by_id.get(video_id)
        if not item or not _is_playable(item):
            continue
        result = _to_result(item)
        if result["thumbnail_url"]:
            results.append(result)
    return results


def _is_playable(item: dict) -> bool:
    status = item.get("status", {})
    return (
        status.get("embeddable", False)
        and status.get("privacyStatus") == "public"
        and status.get("uploadStatus") == "processed"
    )


def _to_result(item: dict) -> dict:
    snippet = item.get("snippet", {})
    thumbnails = snippet.get("thumbnails", {})
    best = (
        thumbnails.get("maxres")
        or thumbnails.get("standard")
        or thumbnails.get("high")
        or thumbnails.get("medium")
        or thumbnails.get("default")
        or {}
    )
    match = _DURATION_PATTERN.fullmatch(item.get("contentDetails", {}).get("duration", "PT0S"))
    hours, minutes, seconds = (int(part or 0) for part in match.groups()) if match else (0, 0, 0)
    return {
        "video_id": item["id"],
        "title": snippet.get("title", "Untitled video"),
        "channel": snippet.get("channelTitle", "YouTube"),
        "duration_seconds": hours * 3600 + minutes * 60 + seconds,
        "description": snippet.get("description", ""),
        "thumbnail_url": best.get("url", ""),
        "url": f"https://www.youtube.com/watch?v={item['id']}",
        "tags": snippet.get("tags", [])[:10],
        "published_at": snippet.get("publishedAt", datetime.now(timezone.utc).isoformat()),
    }


def get_video_details(video_id: str) -> dict | None:
    settings = get_settings()
    if not settings.youtube_configured:
        return None
    try:
        response = httpx.get(
            VIDEOS_URL,
            params={"part": "snippet,contentDetails,status", "id": video_id, "key": settings.youtube_api_key},
            timeout=settings.curation_http_timeout,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return None
    items = response.json().get("items", [])
    return _to_result(items[0]) if items and _is_playable(items[0]) else None
