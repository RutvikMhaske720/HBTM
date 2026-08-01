"""Content router — browse media library, detail, and interaction recording."""

from fastapi import APIRouter, Depends, HTTPException

from app.agents.content_ingestion import fetch_more_like_this
from app.api.schemas import ContentItemOut, FeedbackPayload, MoreLikeThisPayload
from app.db.database import Store, get_db
from app.mcp_tools import internal_db
from app.config import get_settings

router = APIRouter(prefix="/api/v1/content", tags=["content"])


def _item_to_out(item: dict, viewed_ids: set[str] | None = None) -> ContentItemOut:
    return ContentItemOut(
        id=item["id"],
        title=item["title"],
        content_type=item["content_type"],
        domain=item["domain"],
        description=item["description"],
        growth_potential_score=item["growth_potential_score"],
        difficulty=item["difficulty"],
        duration_minutes=item["duration_minutes"],
        mood=item["mood"],
        source=item["source"],
        url=item.get("url", ""),
        thumbnail_url=item.get("thumbnail_url", ""),
        video_id=item.get("video_id", ""),
        published_at=item["published_at"],
        viewed=item["id"] in (viewed_ids or set()),
        # External providers can be previewed in their official embeddable players.
        preview_available=bool(item.get("video_id")) or (
            item.get("source") == "spotify" and "open.spotify.com/track/" in item.get("url", "")
        ),
    )


@router.get("", response_model=list[ContentItemOut])
def list_content(
    domain: str | None = None,
    content_type: str | None = None,
    difficulty: str | None = None,
    user_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Store = Depends(get_db),
):
    """Browse the content library with optional filters."""
    def matches(item: dict) -> bool:
        if domain and item["domain"] != domain:
            return False
        if content_type and item["content_type"] != content_type:
            return False
        if difficulty and item["difficulty"] != difficulty:
            return False
        return True

    items = db.content_items.filter(matches)[offset : offset + limit]
    viewed_ids = internal_db.get_viewed_content_ids(db, user_id) if user_id else set()
    return [_item_to_out(item, viewed_ids) for item in items]


@router.post("/more-like-this", response_model=list[ContentItemOut])
def get_more_like_this(payload: MoreLikeThisPayload, db: Store = Depends(get_db)):
    """Persist a small, type-scoped batch from the configured content sources."""
    items = fetch_more_like_this(db, payload.content_type, payload.domain)
    return [_item_to_out(item) for item in items]


@router.get("/{content_id}", response_model=ContentItemOut)
def get_content_item(content_id: str, db: Store = Depends(get_db)):
    item = db.content_items.get(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    return _item_to_out(item)


@router.post("/{content_id}/view", status_code=204)
def record_view(content_id: str, payload: FeedbackPayload, db: Store = Depends(get_db)):
    """Record a content view event."""
    internal_db.record_interaction(db, payload.user_id, content_id, "viewed")
