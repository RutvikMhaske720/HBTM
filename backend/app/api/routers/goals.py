"""Goals router — CRUD for user goals."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import GoalCreatePayload, GoalOut, GoalSuggestionOut, GoalUpdatePayload
from app.db.database import Store, get_db
from app.db.models import new_goal
from app.mcp_tools import goal_db

router = APIRouter(prefix="/api/v1/goals", tags=["goals"])


def _goal_to_out(goal: dict) -> GoalOut:
    return GoalOut(
        id=goal["id"],
        domain=goal["domain"],
        title=goal["title"],
        timeline=goal["timeline"],
        progress=goal["progress"],
        status=goal["status"],
        created_at=goal["created_at"],
    )


@router.get("/suggestions", response_model=list[GoalSuggestionOut])
def get_goal_suggestions():
    """Starter goal titles per domain — lets onboarding pre-fill an editable,
    specific goal instead of just resending the domain name as the title."""
    return [GoalSuggestionOut(**s) for s in goal_db.suggest_goals("")]


@router.get("/{user_id}", response_model=list[GoalOut])
def get_goals(user_id: str, db: Store = Depends(get_db)):
    goals = db.goals.filter(lambda g: g["user_id"] == user_id and g["status"] == "active")
    return [_goal_to_out(g) for g in goals]


@router.post("/{user_id}", response_model=GoalOut, status_code=201)
def create_goal(user_id: str, payload: GoalCreatePayload, db: Store = Depends(get_db)):
    goal = new_goal(
        user_id=user_id,
        domain=payload.domain,
        title=payload.title,
        timeline=payload.timeline,
        progress=0.0,
        status="active",
    )
    db.goals.upsert(goal)
    return _goal_to_out(goal)


@router.patch("/{goal_id}", response_model=GoalOut)
def update_goal(goal_id: str, payload: GoalUpdatePayload, db: Store = Depends(get_db)):
    goal = db.goals.get(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    if payload.progress is not None:
        goal["progress"] = max(0.0, min(1.0, payload.progress))
    if payload.status is not None:
        goal["status"] = payload.status
    if payload.title is not None:
        goal["title"] = payload.title
    db.goals.upsert(goal)
    return _goal_to_out(goal)


@router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: str, db: Store = Depends(get_db)):
    goal = db.goals.get(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    goal["status"] = "completed"
    db.goals.upsert(goal)
