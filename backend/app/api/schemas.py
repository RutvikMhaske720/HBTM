"""Pydantic request/response models for the FastAPI layer."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ─── Request Models ────────────────────────────────────────────────────────────

class OnboardingPayload(BaseModel):
    current_self: list[str] = Field(default_factory=list)
    imagined_self: list[str] = Field(default_factory=list)
    current_self_notes: str = ""
    imagined_self_notes: str = ""
    learning_styles: list[str] = Field(default_factory=list)
    media_types: list[str] = Field(default_factory=list)
    name: str = ""
    profile_name: str = ""
    email: str = ""
    phone: str = ""
    goals: list[str] = Field(default_factory=list)
    goal_domains: list[str] = Field(default_factory=list)
    timeline: str = "Ongoing"


class FeedbackPayload(BaseModel):
    user_id: str
    content_id: str
    interaction_type: str  # thumbs_up | thumbs_down | done | save | not_for_me | too_easy | too_advanced | viewed


class RunRequest(BaseModel):
    user_id: str
    trigger_type: str = "user_request"


class GoalCreatePayload(BaseModel):
    domain: str
    title: str
    timeline: str = "Ongoing"


class GoalUpdatePayload(BaseModel):
    progress: float | None = None
    status: str | None = None
    title: str | None = None


class ProfileUpdatePayload(BaseModel):
    name: str | None = None
    profile_name: str | None = None
    email: str | None = None
    photo_url: str | None = None


# ─── Response Models ───────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: str
    name: str
    profile_name: str
    email: str
    photo_url: str
    created_at: datetime

    class Config:
        from_attributes = True


class OnboardingResponse(BaseModel):
    user_id: str
    name: str


class ScoreBreakdown(BaseModel):
    goal_alignment: float
    identity_match: float
    growth_potential: float
    recency: float
    feedback: float


class RecommendationOut(BaseModel):
    id: str
    title: str
    content_type: str
    domain: str
    description: str
    growth_potential_score: float
    difficulty: str
    duration_minutes: int
    mood: str
    source: str
    url: str
    why_recommended: str
    score: float
    score_breakdown: ScoreBreakdown | None = None
    run_id: str | None = None


class GoalOut(BaseModel):
    id: str
    domain: str
    title: str
    timeline: str
    progress: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class GoalSuggestionOut(BaseModel):
    domain: str
    suggested_title: str


class FeedbackCountOut(BaseModel):
    count: int


class ContentItemOut(BaseModel):
    id: str
    title: str
    content_type: str
    domain: str
    description: str
    growth_potential_score: float
    difficulty: str
    duration_minutes: int
    mood: str
    source: str
    url: str

    class Config:
        from_attributes = True


class IdentityNodeOut(BaseModel):
    id: str
    node_type: str
    label: str
    weight: float
    source: str
    polarity: str


class IdentityGraphOut(BaseModel):
    user_id: str
    nodes: list[IdentityNodeOut]
    edges: list[dict]


class AgentStepOut(BaseModel):
    agent_name: str
    status: str
    duration_ms: int
    detail: dict[str, Any]
    created_at: datetime | None = None


class AgentRunOut(BaseModel):
    id: str
    user_id: str
    trigger_type: str
    status: str
    confidence_score: float
    started_at: datetime
    finished_at: datetime | None
    steps: list[AgentStepOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


class AgentStatusOut(BaseModel):
    status: str  # "running" | "completed" | "failed" | "idle"
    run_id: str | None = None
    confidence_score: float | None = None
    last_run_at: datetime | None = None


class RunTriggerResponse(BaseModel):
    run_id: str
    status: str
    message: str
