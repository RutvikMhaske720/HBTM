"""Evaluation / Reflection Agent (spec section 6.2.8) — post-cycle quality
check. Computes the confidence score (spec 9.4) that decides whether the
graph routes straight to output or through human_approval first.
"""

from app.agents.state import IABTMAgentState
from app.scoring.formulas import compute_confidence

CONFIDENCE_THRESHOLD = 0.6


def run(state: IABTMAgentState) -> tuple[dict, dict]:
    feedback_history = state.get("feedback_history", [])
    identity_summary = state.get("identity_summary", "")
    goals = state.get("active_goals", [])

    identity_present = 0.0 if identity_summary.startswith("No identity signal") else 1.0
    goals_present = 1.0 if goals else 0.3
    profile_completeness = (identity_present + goals_present) / 2

    feedback_signal_quality = min(len(feedback_history) / 20, 1.0) if feedback_history else 0.2

    confidence = compute_confidence(len(feedback_history), profile_completeness, feedback_signal_quality)

    updates = {
        "confidence_score": confidence,
        "needs_human_approval": confidence < CONFIDENCE_THRESHOLD,
    }
    detail = {
        "confidence_score": round(confidence, 3),
        "profile_completeness": round(profile_completeness, 3),
        "feedback_signal_quality": round(feedback_signal_quality, 3),
        "routed_to": "human_approval" if confidence < CONFIDENCE_THRESHOLD else "output",
    }
    return updates, detail
