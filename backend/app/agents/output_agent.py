"""Output formatter — assembles the final API response (spec `output` node)."""

from app.agents.state import IABTMAgentState


def run(state: IABTMAgentState) -> tuple[dict, dict]:
    final_output = {
        "recommendations": state.get("ranked_recommendations", []),
        "identity_summary": state.get("identity_summary", ""),
        "confidence_score": state.get("confidence_score", 0.0),
        "safety_report": state.get("safety_report", {}),
        "notification": state.get("notification"),
    }
    updates = {"final_output": final_output}
    detail = {"recommendation_count": len(final_output["recommendations"])}
    return updates, detail
