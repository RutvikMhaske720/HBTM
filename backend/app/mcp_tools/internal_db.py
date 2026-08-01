"""MCP: Internal DB Server (spec section 8.2.3). Real implementation —
this is IABTM's own data, so there's no external credential to mock. Each
function takes a SQLAlchemy `Session` as its first argument (the spec's
tool signatures assume an ambient connection; here it's passed explicitly
for testability).
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db.models import AgentRun, AgentStepLog, ContentItem, Goal, IdentityNode, InteractionEvent, User


def get_user_profile(db: Session, user_id: str) -> dict | None:
    user = db.get(User, user_id)
    if not user:
        return None
    return {
        "id": user.id,
        "name": user.name,
        "profile_name": user.profile_name,
        "email": user.email,
        "phone": user.phone,
        "photo_url": user.photo_url,
    }


def get_identity_graph(db: Session, user_id: str) -> dict:
    nodes = db.query(IdentityNode).filter(IdentityNode.user_id == user_id).all()
    return {
        "nodes": [
            {
                "id": n.id,
                "type": n.node_type,
                "label": n.label,
                "weight": n.weight,
                "source": n.source,
                "polarity": n.polarity,
            }
            for n in nodes
        ],
        # Edges are derived (current <-> imagined pairing) rather than stored,
        # since the onboarding flow doesn't declare explicit relationships yet.
        "edges": [],
    }


def update_identity_graph(db: Session, user_id: str, patch: list[dict]) -> dict:
    for entry in patch:
        node = IdentityNode(
            user_id=user_id,
            node_type=entry["node_type"],
            label=entry["label"],
            weight=entry.get("weight", 1.0),
            source=entry.get("source", "self_declared"),
            polarity=entry.get("polarity", "current"),
        )
        db.add(node)
    db.commit()
    return get_identity_graph(db, user_id)


def get_content_item(db: Session, content_id: str) -> dict | None:
    item = db.get(ContentItem, content_id)
    if not item:
        return None
    return _content_item_to_dict(item)


def search_content_library(db: Session, filters: dict | None = None) -> list[dict]:
    filters = filters or {}
    query = db.query(ContentItem)
    if domain := filters.get("domain"):
        query = query.filter(ContentItem.domain == domain)
    if content_type := filters.get("content_type"):
        query = query.filter(ContentItem.content_type == content_type)
    exclude_ids = filters.get("exclude_ids") or []
    items = [i for i in query.all() if i.id not in exclude_ids]
    return [_content_item_to_dict(i) for i in items]


def log_agent_run(db: Session, run_id: str, agent_name: str, status: str, duration_ms: int, detail: dict) -> None:
    db.add(
        AgentStepLog(
            run_id=run_id,
            agent_name=agent_name,
            status=status,
            duration_ms=duration_ms,
            detail=detail,
        )
    )
    db.commit()


def get_feedback_history(db: Session, user_id: str, time_range_days: int = 90) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=time_range_days)
    events = (
        db.query(InteractionEvent)
        .filter(InteractionEvent.user_id == user_id, InteractionEvent.created_at >= cutoff)
        .all()
    )
    return [
        {"content_id": e.content_id, "interaction_type": e.interaction_type, "created_at": e.created_at.isoformat()}
        for e in events
    ]


def record_interaction(db: Session, user_id: str, content_id: str, interaction_type: str) -> None:
    db.add(InteractionEvent(user_id=user_id, content_id=content_id, interaction_type=interaction_type))
    db.commit()


def _content_item_to_dict(item: ContentItem) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "content_type": item.content_type,
        "domain": item.domain,
        "description": item.description,
        "growth_potential_score": item.growth_potential_score,
        "difficulty": item.difficulty,
        "duration_minutes": item.duration_minutes,
        "mood": item.mood,
        "source": item.source,
        "published_at": item.published_at.isoformat(),
        "embedding": item.embedding,
    }
