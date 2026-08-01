"""MCP: Internal DB Server (spec section 8.2.3). Real implementation —
this is IABTM's own data, so there's no external credential to mock. Each
function takes the local `Store` as its first argument (the spec's tool
signatures assume an ambient connection; here it's passed explicitly for
testability) — this is the seam to swap for a real Postgres/Mongo client
later without touching any caller.
"""

from datetime import datetime, timedelta, timezone

from app.db.database import Store
from app.db.models import new_agent_step_log, new_identity_node, new_interaction_event


def get_user_profile(db: Store, user_id: str) -> dict | None:
    user = db.users.get(user_id)
    if not user:
        return None
    return {
        "id": user["id"],
        "name": user["name"],
        "profile_name": user["profile_name"],
        "email": user["email"],
        "phone": user["phone"],
        "photo_url": user["photo_url"],
    }


def get_identity_graph(db: Store, user_id: str) -> dict:
    nodes = db.identity_nodes.filter(lambda n: n["user_id"] == user_id)
    return {
        "nodes": [
            {
                "id": n["id"],
                "type": n["node_type"],
                "label": n["label"],
                "weight": n["weight"],
                "source": n["source"],
                "polarity": n["polarity"],
            }
            for n in nodes
        ],
        # Edges are derived (current <-> imagined pairing) rather than stored,
        # since the onboarding flow doesn't declare explicit relationships yet.
        "edges": [],
    }


def update_identity_graph(db: Store, user_id: str, patch: list[dict]) -> dict:
    for entry in patch:
        node = new_identity_node(
            user_id=user_id,
            node_type=entry["node_type"],
            label=entry["label"],
            weight=entry.get("weight", 1.0),
            source=entry.get("source", "self_declared"),
            polarity=entry.get("polarity", "current"),
        )
        db.identity_nodes.upsert(node)
    return get_identity_graph(db, user_id)


def get_content_item(db: Store, content_id: str) -> dict | None:
    item = db.content_items.get(content_id)
    return _content_item_to_dict(item) if item else None


def search_content_library(db: Store, filters: dict | None = None) -> list[dict]:
    filters = filters or {}
    domain = filters.get("domain")
    content_type = filters.get("content_type")
    exclude_ids = set(filters.get("exclude_ids") or [])

    def matches(item: dict) -> bool:
        if domain and item["domain"] != domain:
            return False
        if content_type and item["content_type"] != content_type:
            return False
        if item["id"] in exclude_ids:
            return False
        return True

    items = db.content_items.filter(matches)
    return [_content_item_to_dict(i) for i in items]


def log_agent_run(db: Store, run_id: str, agent_name: str, status: str, duration_ms: int, detail: dict) -> None:
    step = new_agent_step_log(run_id=run_id, agent_name=agent_name, status=status, duration_ms=duration_ms, detail=detail)
    db.agent_step_logs.upsert(step)


def get_feedback_history(db: Store, user_id: str, time_range_days: int = 90) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=time_range_days)

    def in_range(event: dict) -> bool:
        return event["user_id"] == user_id and datetime.fromisoformat(event["created_at"]) >= cutoff

    events = db.interaction_events.filter(in_range)
    return [
        {"content_id": e["content_id"], "interaction_type": e["interaction_type"], "created_at": e["created_at"]}
        for e in events
    ]


def get_viewed_content_ids(db: Store, user_id: str) -> set[str]:
    """Return every catalogue item this user has opened."""
    return {
        event["content_id"]
        for event in db.interaction_events.filter(
            lambda event: event["user_id"] == user_id and event["interaction_type"] == "viewed"
        )
    }


def record_interaction(db: Store, user_id: str, content_id: str, interaction_type: str) -> None:
    event = new_interaction_event(user_id=user_id, content_id=content_id, interaction_type=interaction_type)
    db.interaction_events.upsert(event)


def _content_item_to_dict(item: dict) -> dict:
    return {
        "id": item["id"],
        "title": item["title"],
        "content_type": item["content_type"],
        "domain": item["domain"],
        "description": item["description"],
        "growth_potential_score": item["growth_potential_score"],
        "difficulty": item["difficulty"],
        "duration_minutes": item["duration_minutes"],
        "mood": item["mood"],
        "source": item["source"],
        "published_at": item["published_at"],
        "embedding": item["embedding"],
    }
