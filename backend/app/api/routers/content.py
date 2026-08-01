"""Content router — browse the curated library, curate more, record views.

Two guarantees hold for everything this router returns:

* **it can be opened** — a real, public source link;
* **it can be previewed** — an embeddable player or a real image.

Items that predate those rules (or whose source has since gone away) are
filtered out on read rather than served with a dead button.
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.agents.content_ingestion import fetch_more_like_this
from app.api.schemas import (
    ContentItemOut,
    CurationReport,
    CurationResult,
    FeedbackPayload,
    MoreLikeThisPayload,
)
from app.curation.profile import build_profile
from app.db.database import Store, get_db
from app.embeddings.index import CONTENT_COLLECTION
from app.mcp_tools import internal_db, semantic_search, web_search

router = APIRouter(prefix="/api/v1/content", tags=["content"])

# Below this, a browse request curates live rather than showing a thin shelf.
MIN_SHELF_SIZE = 4


def _has_preview(item: dict) -> bool:
    """An item is previewable if it can be played inline or shows a real image."""
    if item.get("video_id"):
        return True
    if item.get("source") == "spotify" and "open.spotify.com/track/" in item.get("url", ""):
        return True
    return web_search.is_public_http_url(item.get("thumbnail_url", ""))


def _is_openable(item: dict) -> bool:
    return web_search.is_public_http_url(item.get("url", ""))


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
        preview_available=_has_preview(item),
    )


def _to_report(raw: dict) -> CurationReport:
    known = {"content_type", "domain", "kept", "fetched"}
    return CurationReport(
        content_type=raw.get("content_type", ""),
        domain=raw.get("domain", ""),
        kept=raw.get("kept", 0),
        fetched=raw.get("fetched", 0),
        rejected={key: value for key, value in raw.items() if key not in known},
    )


@router.get("", response_model=list[ContentItemOut])
def list_content(
    domain: str | None = None,
    content_type: str | None = None,
    difficulty: str | None = None,
    user_id: str | None = None,
    q: str | None = Query(None, description="Semantic search over the library"),
    curate: bool = Query(True, description="Curate live when the shelf is thin"),
    limit: int = 50,
    offset: int = 0,
    db: Store = Depends(get_db),
):
    """Browse the library, optionally by meaning rather than by keyword."""
    viewed_ids = internal_db.get_viewed_content_ids(db, user_id) if user_id else set()

    def usable(item: dict) -> bool:
        return _is_openable(item) and _has_preview(item)

    if q:
        # Semantic search goes through the vector index, with the facet
        # filters applied inside the query rather than after it.
        filters = {"has_preview": True}
        if domain:
            filters["domain"] = domain
        if content_type:
            filters["content_type"] = content_type
        hits = semantic_search.similarity_search(
            db, semantic_search.embed_text(q), collection=CONTENT_COLLECTION,
            top_k=limit + offset, filters=filters,
        )
        items = [item for item in hits if usable(item)][offset : offset + limit]
        return [_item_to_out(item, viewed_ids) for item in items]

    def matches(item: dict) -> bool:
        if domain and item["domain"] != domain:
            return False
        if content_type and item["content_type"] != content_type:
            return False
        if difficulty and item["difficulty"] != difficulty:
            return False
        return usable(item)

    items = db.content_items.filter(matches)

    # A first visit, or a medium never curated for this user, has an empty
    # shelf. Rather than showing nothing, go and fetch it now.
    if curate and content_type and user_id and len(items) < MIN_SHELF_SIZE:
        profile = build_profile(db, user_id)
        fetch_more_like_this(db, content_type, domain, user_id=user_id, profile=profile)
        items = db.content_items.filter(matches)

    items.sort(key=lambda item: item["published_at"], reverse=True)
    page = items[offset : offset + limit]
    return [_item_to_out(item, viewed_ids) for item in page]


@router.post("/more-like-this", response_model=CurationResult)
def get_more_like_this(payload: MoreLikeThisPayload, db: Store = Depends(get_db)):
    """Curate a fresh, profile-matched batch of one medium from live sources."""
    items, report = fetch_more_like_this(
        db, payload.content_type, payload.domain, user_id=payload.user_id
    )
    return CurationResult(items=[_item_to_out(item) for item in items], report=_to_report(report))


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
