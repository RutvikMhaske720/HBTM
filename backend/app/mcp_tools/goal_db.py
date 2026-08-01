"""MCP: Goal DB Server (spec section 8.2.6). Real implementation — first-party
data, stored in the same local JSON store as the Internal DB server.
"""

from app.db.database import Store
from app.db.models import new_goal

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


def get_active_goals(db: Store, user_id: str) -> list[dict]:
    goals = db.goals.filter(lambda g: g["user_id"] == user_id and g["status"] == "active")
    return [_goal_to_dict(g) for g in goals]


def create_goal(db: Store, user_id: str, domain: str, title: str = "", timeline: str = "Ongoing") -> dict:
    goal = new_goal(user_id=user_id, domain=domain, title=title or _DOMAIN_SUGGESTIONS.get(domain, domain), timeline=timeline)
    db.goals.upsert(goal)
    return _goal_to_dict(goal)


def update_goal_progress(db: Store, user_id: str, goal_id: str, progress_delta: float) -> dict | None:
    goal = db.goals.get(goal_id)
    if not goal or goal["user_id"] != user_id:
        return None
    goal["progress"] = max(0.0, min(1.0, goal["progress"] + progress_delta))
    if goal["progress"] >= 1.0:
        goal["status"] = "completed"
    db.goals.upsert(goal)
    return _goal_to_dict(goal)


def complete_milestone(db: Store, user_id: str, goal_id: str, milestone_delta: float = 0.25) -> dict | None:
    return update_goal_progress(db, user_id, goal_id, milestone_delta)


def suggest_goals(identity_summary: str) -> list[dict]:
    # Lightweight heuristic stand-in for an LLM suggestion call — surfaces
    # all domains with their canned starter goal, ranked isn't needed here
    # since the onboarding UI already lets the user pick domains directly.
    return [{"domain": d, "suggested_title": t} for d, t in _DOMAIN_SUGGESTIONS.items()]


def _goal_to_dict(goal: dict) -> dict:
    return {
        "id": goal["id"],
        "domain": goal["domain"],
        "title": goal["title"],
        "timeline": goal["timeline"],
        "progress": goal["progress"],
        "status": goal["status"],
    }
