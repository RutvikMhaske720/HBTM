import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, default="")
    profile_name: Mapped[str] = mapped_column(String, default="")
    email: Mapped[str] = mapped_column(String, default="")
    phone: Mapped[str] = mapped_column(String, default="")
    photo_url: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    identity_nodes: Mapped[list["IdentityNode"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    goals: Mapped[list["Goal"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class IdentityNode(Base):
    """A single node in the user's Identity Graph (spec section 2.3)."""

    __tablename__ = "identity_nodes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    node_type: Mapped[str] = mapped_column(String)  # trait | aspiration | habit | skill | value | archetype
    label: Mapped[str] = mapped_column(String)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    source: Mapped[str] = mapped_column(String, default="self_declared")  # self_declared | behavior_inferred | agent_inferred
    polarity: Mapped[str] = mapped_column(String, default="current")  # current (Me) | imagined (I Am)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    user: Mapped["User"] = relationship(back_populates="identity_nodes")


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    domain: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String, default="")
    timeline: Mapped[str] = mapped_column(String, default="Ongoing")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String, default="active")  # active | completed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    user: Mapped["User"] = relationship(back_populates="goals")


class ContentItem(Base):
    """A single recommendable item in the Media Library (spec section 2.6)."""

    __tablename__ = "content_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String)
    content_type: Mapped[str] = mapped_column(String)  # Film | Music | Art | Animation | Editorial | Print | Podcast
    domain: Mapped[str] = mapped_column(String)  # Career | Creativity | Mindset | Health | Knowledge | ...
    description: Mapped[str] = mapped_column(Text, default="")
    growth_potential_score: Mapped[float] = mapped_column(Float, default=0.5)
    difficulty: Mapped[str] = mapped_column(String, default="accessible")  # accessible | challenging
    duration_minutes: Mapped[int] = mapped_column(default=10)
    mood: Mapped[str] = mapped_column(String, default="reflective")
    source: Mapped[str] = mapped_column(String, default="internal")  # internal | youtube | reddit | web
    url: Mapped[str] = mapped_column(String, default="")
    published_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    embedding: Mapped[list] = mapped_column(JSON, default=list)


class InteractionEvent(Base):
    """Both passive interactions and explicit feedback (thumbs up/down, Done, Save...)."""

    __tablename__ = "interaction_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    content_id: Mapped[str] = mapped_column(ForeignKey("content_items.id"))
    interaction_type: Mapped[str] = mapped_column(String)  # thumbs_up | thumbs_down | done | save | not_for_me | too_easy | too_advanced | viewed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    trigger_type: Mapped[str] = mapped_column(String, default="user_request")
    status: Mapped[str] = mapped_column(String, default="running")  # running | completed | failed
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    steps: Mapped[list["AgentStepLog"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class AgentStepLog(Base):
    __tablename__ = "agent_step_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"))
    agent_name: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="success")  # success | error
    duration_ms: Mapped[int] = mapped_column(default=0)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    run: Mapped["AgentRun"] = relationship(back_populates="steps")
