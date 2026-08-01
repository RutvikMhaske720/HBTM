"""MCP: YouTube Server (spec section 8.2.1).

Mocked per this session's setup — no YouTube Data API key was provided.
Real calls would live behind the `if not settings.youtube_mocked:` branch
using `httpx` against `https://www.googleapis.com/youtube/v3/...` with
`settings.youtube_api_key`; the function signatures below already match
what that branch would return, so wiring it in later doesn't touch callers.
"""

import hashlib
from datetime import datetime, timedelta, timezone

from app.config import get_settings

_MOCK_CHANNELS = ["Better Every Day", "The Growth Lab", "Slow Living Studio", "Focused Mind Media"]


def _seeded_int(seed: str, low: int, high: int) -> int:
    h = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    return low + (h % (high - low + 1))


def search_youtube_videos(query: str, category: str | None = None, max_results: int = 5, safe_search: bool = True) -> list[dict]:
    settings = get_settings()
    if not settings.youtube_mocked:
        raise NotImplementedError("Real YouTube API integration not wired in this session — no API key provided.")

    results = []
    for i in range(max_results):
        seed = f"{query}-{category}-{i}"
        video_id = hashlib.sha1(seed.encode()).hexdigest()[:11]
        results.append(
            {
                "video_id": video_id,
                "title": f"{query.title()}: {['A Practical Guide', 'What Nobody Tells You', 'The Honest Version', 'A Deep Dive', 'Getting Started'][i % 5]}",
                "channel": _MOCK_CHANNELS[_seeded_int(seed, 0, len(_MOCK_CHANNELS) - 1)],
                "duration_seconds": _seeded_int(seed, 180, 1800),
                "description": f"A mocked search result standing in for real YouTube content about '{query}'.",
                "tags": [query.lower(), category or "growth"],
                "published_at": (datetime.now(timezone.utc) - timedelta(days=_seeded_int(seed, 1, 400))).isoformat(),
            }
        )
    return results


def get_video_details(video_id: str) -> dict:
    settings = get_settings()
    if not settings.youtube_mocked:
        raise NotImplementedError("Real YouTube API integration not wired in this session — no API key provided.")
    return {
        "video_id": video_id,
        "title": "Mocked video title",
        "channel": _MOCK_CHANNELS[_seeded_int(video_id, 0, len(_MOCK_CHANNELS) - 1)],
        "duration_seconds": _seeded_int(video_id, 180, 1800),
        "transcript_available": True,
    }


def get_user_watch_history(user_oauth_token: str, time_range: str = "7d") -> list[dict]:
    # No OAuth flow implemented this session — always empty until real auth exists.
    return []


def get_channel_details(channel_id: str) -> dict:
    return {"channel_id": channel_id, "name": "Mocked Channel", "recent_videos": []}


def get_video_transcript(video_id: str, language: str = "en") -> str:
    return f"[mocked transcript for video {video_id}]"
