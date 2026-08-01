"""Content router — browse media library, detail, and interaction recording."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import ContentItemOut, FeedbackPayload
from app.db.database import Store, get_db
from app.mcp_tools import internal_db

router = APIRouter(prefix="/api/v1/content", tags=["content"])


def _item_to_out(item: dict) -> ContentItemOut:
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
    )


@router.get("", response_model=list[ContentItemOut])
def list_content(
    domain: str | None = None,
    content_type: str | None = None,
    difficulty: str | None = None,
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
