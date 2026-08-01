"""Agent runner — orchestrates a full LangGraph run, persists results, and
caches the output so polling /recommendations/{user_id} is fast."""

import threading
import uuid
from datetime import datetime, timezone

from app.agents.graph import get_graph
from app.agents.state import IABTMAgentState
from app.db.database import SessionLocal
from app.db.models import AgentRun

# In-memory cache: user_id -> latest recommendations list
_recommendations_cache: dict[str, list[dict]] = {}
# In-memory cache: run_id -> live step log (for SSE streaming)
_run_step_cache: dict[str, list[dict]] = {}
# run_id -> status
_run_status_cache: dict[str, str] = {}
# user_id -> latest run_id
_user_latest_run: dict[str, str] = {}


def get_cached_recommendations(user_id: str) -> list[dict]:
    return _recommendations_cache.get(user_id, [])


def get_run_steps(run_id: str) -> list[dict]:
    return _run_step_cache.get(run_id, [])


def get_run_status(run_id: str) -> str:
    return _run_status_cache.get(run_id, "unknown")


def get_latest_run_id(user_id: str) -> str | None:
    return _user_latest_run.get(user_id)


def run_agent_for_user(user_id: str, trigger_type: str = "user_request") -> str:
    """
    Synchronously run the full agent graph for the given user.
    Persists AgentRun + steps to DB, caches recommendations.
    Returns the run_id.
    """
    run_id = str(uuid.uuid4())

    # Create AgentRun DB row
    with SessionLocal() as db:
        agent_run = AgentRun(
            id=run_id,
            user_id=user_id,
            trigger_type=trigger_type,
            status="running",
            confidence_score=0.0,
            started_at=datetime.now(timezone.utc),
        )
        db.add(agent_run)
        db.commit()

    _run_status_cache[run_id] = "running"
    _user_latest_run[user_id] = run_id
    _run_step_cache[run_id] = []

    initial_state: IABTMAgentState = {
        "user_id": user_id,
        "run_id": run_id,
        "trigger_type": trigger_type,
        "step_log": [],
        "safety_retry_count": 0,
        "needs_human_approval": False,
        "confidence_score": 0.0,
    }

    try:
        graph = get_graph()
        config = {"configurable": {"thread_id": user_id}}
        final_state = graph.invoke(initial_state, config=config)

        recommendations = final_state.get("ranked_recommendations", [])
        confidence = final_state.get("confidence_score", 0.0)
        step_log = final_state.get("step_log", [])

        # Cache results
        _recommendations_cache[user_id] = recommendations
        _run_step_cache[run_id] = step_log
        _run_status_cache[run_id] = "completed"

        # Update AgentRun row
        with SessionLocal() as db:
            run = db.get(AgentRun, run_id)
            if run:
                run.status = "completed"
                run.confidence_score = confidence
                run.finished_at = datetime.now(timezone.utc)
                db.commit()

    except Exception as exc:  # noqa: BLE001
        _run_status_cache[run_id] = "failed"
        _run_step_cache[run_id].append({
            "agent_name": "Runner",
            "status": "error",
            "duration_ms": 0,
            "detail": {"error": str(exc)},
        })
        with SessionLocal() as db:
            run = db.get(AgentRun, run_id)
            if run:
                run.status = "failed"
                run.finished_at = datetime.now(timezone.utc)
                db.commit()

    return run_id


def run_agent_async(user_id: str, trigger_type: str = "user_request") -> str:
    """Start agent run in background thread. Returns run_id immediately."""
    run_id = str(uuid.uuid4())

    # Create AgentRun DB row eagerly
    with SessionLocal() as db:
        agent_run = AgentRun(
            id=run_id,
            user_id=user_id,
            trigger_type=trigger_type,
            status="running",
            confidence_score=0.0,
            started_at=datetime.now(timezone.utc),
        )
        db.add(agent_run)
        db.commit()

    _run_status_cache[run_id] = "running"
    _user_latest_run[user_id] = run_id
    _run_step_cache[run_id] = []

    def _run():
        initial_state: IABTMAgentState = {
            "user_id": user_id,
            "run_id": run_id,
            "trigger_type": trigger_type,
            "step_log": [],
            "safety_retry_count": 0,
            "needs_human_approval": False,
            "confidence_score": 0.0,
        }
        try:
            graph = get_graph()
            config = {"configurable": {"thread_id": f"{user_id}:{run_id}"}}
            final_state = graph.invoke(initial_state, config=config)

            recommendations = final_state.get("ranked_recommendations", [])
            confidence = final_state.get("confidence_score", 0.0)
            step_log = final_state.get("step_log", [])

            _recommendations_cache[user_id] = recommendations
            _run_step_cache[run_id] = step_log
            _run_status_cache[run_id] = "completed"

            with SessionLocal() as db:
                run = db.get(AgentRun, run_id)
                if run:
                    run.status = "completed"
                    run.confidence_score = confidence
                    run.finished_at = datetime.now(timezone.utc)
                    db.commit()

        except Exception as exc:  # noqa: BLE001
            _run_status_cache[run_id] = "failed"
            _run_step_cache[run_id].append({
                "agent_name": "Runner",
                "status": "error",
                "duration_ms": 0,
                "detail": {"error": str(exc)},
            })
            with SessionLocal() as db:
                run = db.get(AgentRun, run_id)
                if run:
                    run.status = "failed"
                    run.finished_at = datetime.now(timezone.utc)
                    db.commit()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return run_id
