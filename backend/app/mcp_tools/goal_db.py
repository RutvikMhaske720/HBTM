"""MCP: Goal DB Server (spec section 8.2.6). Real implementation — first-party
data, part of the same SQLite database as the Internal DB server.
"""

from sqlalchemy.orm import Session

from app.db.models import Goal

_DOMAIN_SUGGESTIONS = {
    "Career": "Build one visible portfolio piece",
    "Creativity": "Ship something small every week",
    "Mindset": "Protect one hour of deep focus daily",
    "Health": "Move your body five days a week",
    "Knowledge": "Finish one long-form resource a month",
    "Relationships": "Have one repair conversation you've been avoiding",
    "Finance": "Automate one recurring saving",
    "Purpose": "Write down what 'enough' looks like",
}


def get_active_goals(db: Session, user_id: str) -> list[dict]:
    goals = db.query(Goal).filter(Goal.user_id == user_id, Goal.status == "active").all()
    return [_goal_to_dict(g) for g in goals]


def create_goal(db: Session, user_id: str, domain: str, title: str = "", timeline: str = "Ongoing") -> dict:
    goal = Goal(user_id=user_id, domain=domain, title=title or _DOMAIN_SUGGESTIONS.get(domain, domain), timeline=timeline)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return _goal_to_dict(goal)


def update_goal_progress(db: Session, user_id: str, goal_id: str, progress_delta: float) -> dict | None:
    goal = db.get(Goal, goal_id)
    if not goal or goal.user_id != user_id:
        return None
    goal.progress = max(0.0, min(1.0, goal.progress + progress_delta))
    if goal.progress >= 1.0:
        goal.status = "completed"
    db.commit()
    db.refresh(goal)
    return _goal_to_dict(goal)


def complete_milestone(db: Session, user_id: str, goal_id: str, milestone_delta: float = 0.25) -> dict | None:
    return update_goal_progress(db, user_id, goal_id, milestone_delta)


def suggest_goals(identity_summary: str) -> list[dict]:
    # Lightweight heuristic stand-in for an LLM suggestion call — surfaces
    # all domains with their canned starter goal, ranked isn't needed here
    # since the onboarding UI already lets the user pick domains directly.
    return [{"domain": d, "suggested_title": t} for d, t in _DOMAIN_SUGGESTIONS.items()]


def _goal_to_dict(goal: Goal) -> dict:
    return {
        "id": goal.id,
        "domain": goal.domain,
        "title": goal.title,
        "timeline": goal.timeline,
        "progress": goal.progress,
        "status": goal.status,
    }
