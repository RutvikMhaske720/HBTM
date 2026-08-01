"""Recommendations router."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.agents import runner as agent_runner
from app.api.schemas import FeedbackCountOut, FeedbackPayload, RecommendationOut, RunTriggerResponse, ScoreBreakdown
from app.db.database import Store, get_db
from app.mcp_tools import internal_db

router = APIRouter(prefix="/api/v1", tags=["recommendations"])


def _to_rec_out(item: dict, run_id: str | None = None) -> RecommendationOut:
    breakdown = item.get("score_breakdown")
    return RecommendationOut(
        id=item.get("id", ""),
        title=item.get("title", ""),
        content_type=item.get("content_type", ""),
        domain=item.get("domain", ""),
        description=item.get("description", ""),
        growth_potential_score=item.get("growth_potential_score", 0.0),
        difficulty=item.get("difficulty", "accessible"),
        duration_minutes=item.get("duration_minutes", 0),
        mood=item.get("mood", ""),
        source=item.get("source", "internal"),
        url=item.get("url", ""),
        why_recommended=item.get("why_recommended", ""),
        score=item.get("score", 0.0),
        score_breakdown=ScoreBreakdown(**breakdown) if breakdown else None,
        run_id=run_id,
    )


@router.get("/recommendations/{user_id}", response_model=list[RecommendationOut])
def get_recommendations(user_id: str, db: Store = Depends(get_db)):
    """Return cached feed. If no cache exists, trigger a fresh run synchronously."""
    cached = agent_runner.get_cached_recommendations(user_id)
    run_id = agent_runner.get_latest_run_id(user_id)

    if not cached:
        # First time — run synchronously so we return real data
        run_id = agent_runner.run_agent_for_user(user_id)
        cached = agent_runner.get_cached_recommendations(user_id)

    return [_to_rec_out(item, run_id) for item in cached]


@router.post("/recommendations/refresh", response_model=RunTriggerResponse)
def refresh_recommendations(body: dict, background_tasks: BackgroundTasks, db: Store = Depends(get_db)):
    """
    Trigger a fresh agent run in the background.
    Returns the run_id immediately so the frontend can poll status.
    """
    user_id = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=422, detail="user_id required")

    run_id = agent_runner.run_agent_async(user_id, trigger_type="user_request")
    return RunTriggerResponse(
        run_id=run_id,
        status="running",
        message="Agent run started — poll /agent/status/{user_id} for updates",
    )


@router.post("/recommendations/{content_id}/feedback", status_code=204)
def submit_feedback(content_id: str, payload: FeedbackPayload, db: Store = Depends(get_db)):
    """Record a user feedback signal (thumbs up/down, done, save, etc.)."""
    internal_db.record_interaction(db, payload.user_id, content_id, payload.interaction_type)


@router.get("/recommendations/{user_id}/feedback-count", response_model=FeedbackCountOut)
def get_feedback_count(user_id: str, db: Store = Depends(get_db)):
    """All-time feedback count — surfaced on the dashboard so giving feedback
    visibly feels like it's shaping the curator, not disappearing into a void."""
    count = len(internal_db.get_feedback_history(db, user_id, time_range_days=3650))
    return FeedbackCountOut(count=count)
