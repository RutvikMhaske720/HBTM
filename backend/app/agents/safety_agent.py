"""Safety Agent (spec section 6.2.7).

Rule-based classifier standing in for the spec's "internal LLM
classifier" (no model API key this session). Flags anything with a very
low editorial growth_potential_score as engagement-bait / low-quality —
the seed library includes two deliberately bad items so this has
something real to catch — and re-scores by multiplying in the safety
factor before re-sorting.
"""

from app.agents.state import IABTMAgentState

UNSAFE_GROWTH_THRESHOLD = 0.3
KEEP_TOP_N = 10


def _safety_factor(item: dict) -> float:
    if item["growth_potential_score"] < UNSAFE_GROWTH_THRESHOLD:
        return 0.0
    return 1.0


def run(state: IABTMAgentState) -> tuple[dict, dict]:
    ranked = state.get("ranked_recommendations", [])

    flagged = []
    rescored = []
    for item in ranked:
        factor = _safety_factor(item)
        if factor == 0.0:
            flagged.append({"id": item["id"], "title": item["title"], "reason": "growth_potential below safety threshold"})
            continue
        rescored.append({**item, "score": item["score"] * factor})

    rescored.sort(key=lambda x: x["score"], reverse=True)
    kept = rescored[:KEEP_TOP_N]

    retry_count = state.get("safety_retry_count", 0)
    majority_flagged = bool(ranked) and len(flagged) > len(ranked) / 2
    # Only allow one re-fetch loop back to content_retrieve — never loop forever.
    passed = not majority_flagged or retry_count >= 1

    safety_report = {"checked": len(ranked), "flagged_count": len(flagged), "flagged": flagged, "passed": passed}

    updates = {
        "ranked_recommendations": kept,
        "safety_report": safety_report,
        "safety_retry_count": retry_count + (0 if passed else 1),
    }
    detail = {"checked": len(ranked), "flagged": len(flagged), "kept": len(kept), "passed": passed}
    return updates, detail
