"""Goals router — CRUD for user goals."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import GoalCreatePayload, GoalOut, GoalUpdatePayload
from app.db.database import get_db
from app.db.models import Goal

router = APIRouter(prefix="/api/v1/goals", tags=["goals"])


def _goal_to_out(goal: Goal) -> GoalOut:
    return GoalOut(
        id=goal.id,
        domain=goal.domain,
        title=goal.title,
        timeline=goal.timeline,
        progress=goal.progress,
        status=goal.status,
        created_at=goal.created_at,
    )


@router.get("/{user_id}", response_model=list[GoalOut])
def get_goals(user_id: str, db: Session = Depends(get_db)):
    goals = db.query(Goal).filter(Goal.user_id == user_id, Goal.status == "active").all()
    return [_goal_to_out(g) for g in goals]


@router.post("/{user_id}", response_model=GoalOut, status_code=201)
def create_goal(user_id: str, payload: GoalCreatePayload, db: Session = Depends(get_db)):
    goal = Goal(
        user_id=user_id,
        domain=payload.domain,
        title=payload.title,
        timeline=payload.timeline,
        progress=0.0,
        status="active",
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return _goal_to_out(goal)


@router.patch("/{goal_id}", response_model=GoalOut)
def update_goal(goal_id: str, payload: GoalUpdatePayload, db: Session = Depends(get_db)):
    goal = db.get(Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    if payload.progress is not None:
        goal.progress = max(0.0, min(1.0, payload.progress))
    if payload.status is not None:
        goal.status = payload.status
    if payload.title is not None:
        goal.title = payload.title
    db.commit()
    db.refresh(goal)
    return _goal_to_out(goal)


@router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: str, db: Session = Depends(get_db)):
    goal = db.get(Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    goal.status = "completed"
    db.commit()
