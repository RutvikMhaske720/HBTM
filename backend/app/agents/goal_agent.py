"""Goal Agent (spec section 6.2.5)."""

from app.agents.state import IABTMAgentState
from app.db.database import SessionLocal
from app.mcp_tools import goal_db


def run(state: IABTMAgentState) -> tuple[dict, dict]:
    user_id = state["user_id"]
    with SessionLocal() as db:
        goals = goal_db.get_active_goals(db, user_id)

    updates = {"active_goals": goals}
    detail = {"active_goal_count": len(goals), "domains": [g["domain"] for g in goals]}
    return updates, detail
