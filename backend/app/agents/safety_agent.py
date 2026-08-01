"""Safety Agent (spec section 6.2.7).

A rule-based classifier standing in for the spec's internal LLM classifier.
Now that the pool is real external media rather than a hand-written
catalogue, the checks that matter have changed: the failure modes are dead
links, missing previews, insecure sources, and engagement bait — not an
editorially-assigned low score.

Each check contributes a multiplier. An item that fails a hard check is
dropped outright; softer signals just push it down the ranking.
"""

from urllib.parse import urlparse

from app.agents.state import IABTMAgentState

UNSAFE_GROWTH_THRESHOLD = 0.3
KEEP_TOP_N = 10

_BAIT_MARKERS = (
    "you won't believe", "shocking", "one weird trick", "gurus hide",
    "doctors hate", "get rich quick", "100% guaranteed", "miracle",
)
_CLAIM_MARKERS = ("cure", "overnight", "guaranteed returns", "risk-free", "instantly")


def _assess(item: dict) -> tuple[float, str]:
    """Return `(multiplier, reason)`; a multiplier of 0 removes the item."""
    url = item.get("url", "")
    parsed = urlparse(url)
    title = item.get("title", "").lower()

    # Hard failures — a user cannot act on any of these.
    if not url or parsed.scheme not in {"http", "https"}:
        return 0.0, "no usable source link"
    if not (item.get("thumbnail_url") or item.get("video_id")):
        return 0.0, "no preview available"
    if any(marker in title for marker in _BAIT_MARKERS):
        return 0.0, "engagement-bait title"
    if item.get("growth_potential_score", 0.0) < UNSAFE_GROWTH_THRESHOLD:
        return 0.0, "growth potential below safety threshold"

    # Soft signals — keep, but rank lower.
    multiplier, notes = 1.0, []
    if parsed.scheme == "http":
        multiplier *= 0.8
        notes.append("insecure source")
    if any(marker in title for marker in _CLAIM_MARKERS):
        multiplier *= 0.7
        notes.append("unverifiable claim language")
    return multiplier, ", ".join(notes)


def run(state: IABTMAgentState) -> tuple[dict, dict]:
    ranked = state.get("ranked_recommendations", [])

    flagged, rescored, downranked = [], [], 0
    for item in ranked:
        multiplier, reason = _assess(item)
        if multiplier == 0.0:
            flagged.append({"id": item["id"], "title": item["title"], "reason": reason})
            continue
        if multiplier < 1.0:
            downranked += 1
        rescored.append({**item, "score": item["score"] * multiplier})

    rescored.sort(key=lambda item: item["score"], reverse=True)
    kept = rescored[:KEEP_TOP_N]

    retry_count = state.get("safety_retry_count", 0)
    majority_flagged = bool(ranked) and len(flagged) > len(ranked) / 2
    # Only allow one re-fetch loop back to content_retrieve — never loop forever.
    passed = not majority_flagged or retry_count >= 1

    safety_report = {
        "checked": len(ranked),
        "flagged_count": len(flagged),
        "flagged": flagged,
        "downranked_count": downranked,
        "passed": passed,
    }
    updates = {
        "ranked_recommendations": kept,
        "safety_report": safety_report,
        "safety_retry_count": retry_count + (0 if passed else 1),
    }
    detail = {
        "checked": len(ranked), "flagged": len(flagged),
        "downranked": downranked, "kept": len(kept), "passed": passed,
    }
    return updates, detail
