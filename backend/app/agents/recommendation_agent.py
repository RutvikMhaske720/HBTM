"""Recommendation Agent (spec section 6.2.3) — the core ranking step.

Runs the full spec 9.3 scoring formula per candidate (safety_factor left
at 1.0 here; the Safety Agent applies the real multiplier next) and
attaches a one-sentence, user-facing "why recommended" explanation, as
required by the agent's system prompt in the spec.
"""

from datetime import datetime, timezone

from app.agents.state import IABTMAgentState
from app.mcp_tools import semantic_search
from app.scoring.formulas import compute_final_score

TOP_N = 20


def _explain(item: dict, breakdown: dict, goal_domains: list[str]) -> str:
    # compute_feedback_factor returns exactly 0.5 as a neutral cold-start
    # prior when there's no feedback history for this domain — anything
    # else means real signal, so a strong value is worth calling out
    # explicitly (feedback should visibly shape future picks, not just
    # silently nudge the score by its 10% weight).
    if breakdown["feedback"] >= 0.7:
        return f"You've responded well to {item['domain']} content before, so we're leaning into more of it."
    if item["domain"] in goal_domains and breakdown["goal_alignment"] >= breakdown["identity_match"]:
        return f"Recommended because it advances your goal in {item['domain']}."
    if breakdown["identity_match"] > 0.15:
        return "Matches the direction you're moving in, based on your current-self / imagined-self profile."
    if breakdown["growth_potential"] >= 0.75:
        return "High growth-potential pick — one of the strongest items in our library for this domain."
    return f"A well-rounded {item['domain'].lower()} pick to keep your path diverse."


def run(state: IABTMAgentState) -> tuple[dict, dict]:
    identity_summary = state.get("identity_summary", "")
    goals = state.get("active_goals", [])
    goal_domains = [g["domain"] for g in goals]
    feedback_history = state.get("feedback_history", [])
    candidates = state.get("candidate_pool", [])

    user_vector = semantic_search.build_user_query_vector(
        identity_summary, [f"{g['domain']} {g['title']}" for g in goals] or ["personal growth"]
    )
    goal_vectors = [semantic_search.embed_text(f"{g['domain']} {g['title']}") for g in goals] or [user_vector]

    now = datetime.now(timezone.utc)
    scored = []
    for item in candidates:
        result = compute_final_score(item, user_vector, goal_vectors, feedback_history, safety_factor=1.0, now=now)
        scored.append(
            {
                **item,
                "score": result["final_score"],
                "score_breakdown": result["breakdown"],
                "why_recommended": _explain(item, result["breakdown"], goal_domains),
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    ranked = scored[:TOP_N]

    updates = {"ranked_recommendations": ranked}
    detail = {"candidates_scored": len(scored), "kept": len(ranked)}
    return updates, detail
