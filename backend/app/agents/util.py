"""Shared plumbing for turning a plain function into a traced LangGraph node.

Every agent node: times itself, writes a row to `agent_step_logs` (so the
Agent Lab / SSE trace has something real to show), and appends a
`StepLogEntry` onto `state.step_log`. Spec section 4.2.4 describes each
node in the trace as `[AgentName] -> did X (N results), Nms` — `detail`
is exactly that payload.
"""

import time
from collections.abc import Callable
from typing import Any

from app.agents.state import IABTMAgentState
from app.db.database import SessionLocal
from app.mcp_tools import internal_db

NodeFn = Callable[[IABTMAgentState], tuple[dict[str, Any], dict[str, Any]]]


def traced_node(agent_name: str, fn: NodeFn) -> Callable[[IABTMAgentState], dict[str, Any]]:
    def node(state: IABTMAgentState) -> dict[str, Any]:
        start = time.perf_counter()
        status = "success"
        detail: dict[str, Any] = {}
        updates: dict[str, Any] = {}
        try:
            updates, detail = fn(state)
        except Exception as exc:  # noqa: BLE001 — agent failures must not crash the graph
            status = "error"
            detail = {"error": str(exc)}
        duration_ms = int((time.perf_counter() - start) * 1000)

        run_id = state.get("run_id")
        if run_id:
            with SessionLocal() as db:
                internal_db.log_agent_run(db, run_id, agent_name, status, duration_ms, detail)

        entry = {"agent_name": agent_name, "status": status, "duration_ms": duration_ms, "detail": detail}
        step_log = [*state.get("step_log", []), entry]
        return {**updates, "step_log": step_log}

    return node
