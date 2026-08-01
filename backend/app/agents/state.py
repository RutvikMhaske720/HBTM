from typing import Any, TypedDict


class StepLogEntry(TypedDict):
    agent_name: str
    status: str
    duration_ms: int
    detail: dict


class IABTMAgentState(TypedDict, total=False):
    # Core identity
    user_id: str
    identity_summary: str

    # Goals
    active_goals: list[dict]

    # Memory
    session_memory: str
    feedback_history: list[dict]

    # Content
    candidate_pool: list[dict]
    ranked_recommendations: list[dict]

    # Safety
    safety_report: dict

    # Output
    notification: dict | None
    final_output: dict[str, Any]

    # Orchestration metadata
    run_id: str
    trigger_type: str
    step_log: list[StepLogEntry]
    confidence_score: float
    needs_human_approval: bool
    safety_retry_count: int
