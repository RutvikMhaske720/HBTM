"""Content router — browse media library, detail, and interaction recording."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import ContentItemOut, FeedbackPayload
from app.db.database import get_db
from app.db.models import ContentItem
from app.mcp_tools import internal_db

router = APIRouter(prefix="/api/v1/content", tags=["content"])


def _item_to_out(item: ContentItem) -> ContentItemOut:
    return ContentItemOut(
        id=item.id,
        title=item.title,
        content_type=item.content_type,
        domain=item.domain,
        description=item.description,
        growth_potential_score=item.growth_potential_score,
        difficulty=item.difficulty,
        duration_minutes=item.duration_minutes,
        mood=item.mood,
        source=item.source,
        url=getattr(item, "url", ""),
    )


@router.get("", response_model=list[ContentItemOut])
def list_content(
    domain: str | None = None,
    content_type: str | None = None,
    difficulty: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Browse the content library with optional filters."""
    query = db.query(ContentItem)
    if domain:
        query = query.filter(ContentItem.domain == domain)
    if content_type:
        query = query.filter(ContentItem.content_type == content_type)
    if difficulty:
        query = query.filter(ContentItem.difficulty == difficulty)
    items = query.offset(offset).limit(limit).all()
    return [_item_to_out(item) for item in items]


@router.get("/{content_id}", response_model=ContentItemOut)
def get_content_item(content_id: str, db: Session = Depends(get_db)):
    item = db.get(ContentItem, content_id)
    if not item:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Content not found")
    return _item_to_out(item)


@router.post("/{content_id}/view", status_code=204)
def record_view(content_id: str, payload: FeedbackPayload, db: Session = Depends(get_db)):
    """Record a content view event."""
    internal_db.record_interaction(db, payload.user_id, content_id, "viewed")
