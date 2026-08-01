"""Small, catalogue-scoped external-content ingestion flow."""

import hashlib

from app.db.database import Store
from app.db.models import new_content_item
from app.mcp_tools import reddit, youtube


def _stable_id(source: str, external_id: str) -> str:
    return f"ext-{hashlib.sha1(f'{source}-{external_id}'.encode()).hexdigest()[:12]}"


def fetch_more_like_this(
    db: Store, content_type: str, domain: str | None = None, max_results: int = 6
) -> list[dict]:
    """Fetch and persist a few source items for one media type.

    The MCP source modules remain the single seam for real-vs-mocked data.
    """
    resolved_domain = domain or "Knowledge"
    query = f"{resolved_domain} {content_type}"
    created: list[dict] = []

    if content_type == "Editorial":
        subreddit = f"r/{resolved_domain}"
        for post in reddit.get_top_posts(subreddit, limit=max_results):
            record = new_content_item(
                id=_stable_id("reddit", post["post_id"]),
                title=post["title"],
                content_type=content_type,
                domain=resolved_domain,
                description=f"Community discussion from {post['subreddit']}.",
                duration_minutes=5,
                mood="curious",
                source="reddit",
                url="",
            )
            created.append(db.content_items.upsert(record))
        return created

    for video in youtube.search_youtube_videos(query=query, category=resolved_domain, max_results=max_results):
        video_id = video["video_id"]
        record = new_content_item(
            id=_stable_id("youtube", video_id),
            title=video["title"],
            content_type=content_type,
            domain=resolved_domain,
            description=video["description"],
            growth_potential_score=0.6,
            difficulty="accessible",
            duration_minutes=max(1, video["duration_seconds"] // 60),
            mood="curious",
            source="youtube",
            url=f"https://www.youtube.com/watch?v={video_id}",
            thumbnail_url=f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            video_id=video_id,
            published_at=video["published_at"],
        )
        created.append(db.content_items.upsert(record))
    return created
