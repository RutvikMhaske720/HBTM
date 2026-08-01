"""Memory Agent (spec section 6.2.4) — loads session + feedback memory.

Session memory would be Redis in production; here it's the in-process
MemoryStore (see app/memory/store.py). Feedback history is enriched with
each content item's domain so the scoring formula's feedback_factor
(section 9.3) can compare like-for-like.
"""

from app.agents.state import IABTMAgentState
from app.db.database import SessionLocal
from app.memory.store import get_memory_store
from app.mcp_tools import internal_db


def run(state: IABTMAgentState) -> tuple[dict, dict]:
    user_id = state["user_id"]
    store = get_memory_store()
    session_memory = store.get(f"session:{user_id}", default="")

    with SessionLocal() as db:
        raw_feedback = internal_db.get_feedback_history(db, user_id)
        enriched = []
        for f in raw_feedback:
            item = internal_db.get_content_item(db, f["content_id"])
            enriched.append({**f, "domain": item["domain"] if item else None})

    updates = {"session_memory": session_memory, "feedback_history": enriched}
    detail = {"feedback_events": len(enriched), "session_memory_present": bool(session_memory)}
    return updates, detail
