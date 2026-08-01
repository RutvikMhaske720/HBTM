"""Small, catalogue-scoped external-content ingestion flow."""

import hashlib

from app.db.database import Store
from app.db.models import new_content_item
from app.mcp_tools import pinterest, reddit, spotify, youtube


def _stable_id(source: str, external_id: str) -> str:
    return f"ext-{hashlib.sha1(f'{source}-{external_id}'.encode()).hexdigest()[:12]}"


def fetch_more_like_this(
    db: Store, content_type: str, domain: str | None = None, max_results: int = 6, goal_titles: list[str] | None = None
) -> list[dict]:
    """Fetch and persist a few source items for one media type.

    The MCP source modules remain the single seam for real-vs-mocked data.
    """
    resolved_domain = domain or "Knowledge"
    goal_context = " ".join(goal_titles or [])
    query = f"{goal_context or resolved_domain} {content_type}"
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

    # Pinterest is a strong fit for visual Art, but only reads Pins from the
    # board the account authorises. Other media types continue to use YouTube.
    if content_type == "Art":
        for pin in pinterest.get_board_pins(limit=max_results):
            record = new_content_item(
                id=_stable_id("pinterest", pin["pin_id"]),
                title=pin["title"],
                content_type="Art",
                domain=resolved_domain,
                description=pin["description"],
                growth_potential_score=0.6,
                difficulty="accessible",
                duration_minutes=5,
                mood="curious",
                source="pinterest",
                url=pin["url"],
                thumbnail_url=pin["image_url"],
                published_at=pin["published_at"],
            )
            created.append(db.content_items.upsert(record))
        if created:
            return created

    if content_type == "Music":
        # Spotify can be temporarily unavailable because of its app/account
        # policy. Keep Music useful by falling back to YouTube in that case.
        try:
            tracks = spotify.search_tracks(query=query, max_results=max_results)
        except Exception:
            tracks = []
        for track in tracks:
            record = new_content_item(
                id=_stable_id("spotify", track["track_id"]),
                title=track["title"], content_type="Music", domain=resolved_domain,
                description=track["description"], growth_potential_score=0.6,
                difficulty="accessible", duration_minutes=max(1, track["duration_seconds"] // 60),
                mood="curious", source="spotify", url=track["url"],
                thumbnail_url=track["thumbnail_url"], published_at=track["published_at"],
            )
            created.append(db.content_items.upsert(record))
        if created:
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
