"""Planning Agent (spec section 6.2.10).

Not part of the per-recommendation LangGraph run in section 7.2 — it's
invoked on demand (e.g. "build me a path") rather than on every cycle, so
it's exposed as a plain function called directly by an API route instead
of a graph node.
"""

from app.mcp_tools import internal_db


def build_path_plan(db, user_id: str, goals: list[dict]) -> dict:
    milestones = []
    for goal in goals:
        candidates = internal_db.search_content_library(db, {"domain": goal["domain"]})
        candidates.sort(key=lambda c: c["growth_potential_score"], reverse=True)
        milestones.append(
            {
                "goal_id": goal["id"],
                "domain": goal["domain"],
                "title": goal["title"],
                "timeline": goal["timeline"],
                "progress": goal["progress"],
                "content_sequence": [c["id"] for c in candidates[:3]],
            }
        )

    return {
        "user_id": user_id,
        "milestones": milestones,
        "estimated_weeks": max(len(milestones) * 2, 4),
    }
