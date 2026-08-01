"""Factory functions for the JSON-backed record shapes (spec section 10.1).

Each returns a `Record` (dict + attribute access) with the same fields the
original SQLAlchemy models exposed, so routers/agents/mcp_tools read and
write them exactly the way they did against the ORM.
"""

import uuid
from datetime import datetime, timezone

from app.db.database import Record


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_user(
    *, id: str | None = None, name: str = "", profile_name: str = "", email: str = "",
    phone: str = "", photo_url: str = "", created_at: str | None = None,
) -> Record:
    return Record(
        id=id or _uuid(), name=name, profile_name=profile_name, email=email,
        phone=phone, photo_url=photo_url, created_at=created_at or _now(),
    )


def new_identity_node(
    *, id: str | None = None, user_id: str, node_type: str, label: str, weight: float = 1.0,
    source: str = "self_declared", polarity: str = "current",
) -> Record:
    now = _now()
    return Record(
        id=id or _uuid(), user_id=user_id, node_type=node_type, label=label,
        weight=weight, source=source, polarity=polarity, created_at=now, updated_at=now,
    )


def new_goal(
    *, id: str | None = None, user_id: str, domain: str, title: str = "", timeline: str = "Ongoing",
    progress: float = 0.0, status: str = "active", created_at: str | None = None,
) -> Record:
    return Record(
        id=id or _uuid(), user_id=user_id, domain=domain, title=title, timeline=timeline,
        progress=progress, status=status, created_at=created_at or _now(),
    )


def new_content_item(
    *, id: str | None = None, title: str, content_type: str, domain: str, description: str = "",
    growth_potential_score: float = 0.5, difficulty: str = "accessible", duration_minutes: int = 10,
    mood: str = "reflective", source: str = "internal", url: str = "",
    thumbnail_url: str = "", video_id: str = "", published_at: str | None = None,
    embedding: list[float] | None = None, relevance_score: float | None = None,
    curated_for: str = "",
) -> Record:
    # `relevance_score` and `curated_for` are provenance: they record that this
    # item cleared the curation gates, and for whose profile. A record without
    # them predates the gates and cannot be assumed to be relevant to anyone.
    return Record(
        id=id or _uuid(), title=title, content_type=content_type, domain=domain, description=description,
        growth_potential_score=growth_potential_score, difficulty=difficulty, duration_minutes=duration_minutes,
        mood=mood, source=source, url=url, thumbnail_url=thumbnail_url, video_id=video_id,
        published_at=published_at or _now(), embedding=embedding or [],
        relevance_score=relevance_score, curated_for=curated_for,
    )


def new_interaction_event(
    *, id: str | None = None, user_id: str, content_id: str, interaction_type: str,
    created_at: str | None = None,
) -> Record:
    return Record(
        id=id or _uuid(), user_id=user_id, content_id=content_id,
        interaction_type=interaction_type, created_at=created_at or _now(),
    )


def new_agent_run(
    *, id: str | None = None, user_id: str, trigger_type: str = "user_request", status: str = "running",
    confidence_score: float = 0.0, started_at: str | None = None, finished_at: str | None = None,
) -> Record:
    return Record(
        id=id or _uuid(), user_id=user_id, trigger_type=trigger_type, status=status,
        confidence_score=confidence_score, started_at=started_at or _now(), finished_at=finished_at,
    )


def new_agent_step_log(
    *, id: str | None = None, run_id: str, agent_name: str, status: str = "success",
    duration_ms: int = 0, detail: dict | None = None, created_at: str | None = None,
) -> Record:
    return Record(
        id=id or _uuid(), run_id=run_id, agent_name=agent_name, status=status,
        duration_ms=duration_ms, detail=detail or {}, created_at=created_at or _now(),
    )
