"""Recommendation scoring (spec section 9.3) and confidence (9.4)."""

import math

from app.embeddings.embedder import get_embedder

W_GOAL, W_IDENTITY, W_GROWTH, W_RECENCY, W_FEEDBACK = 0.30, 0.25, 0.25, 0.10, 0.10

# Stand-in age for an item with no usable date: old enough that recency stops
# helping it, but still rankable on the other four signals.
_UNDATED_AGE_DAYS = 3650.0


def days_since(published_at_iso: str, now) -> float:
    """Age in days, tolerant of the date formats real sources emit.

    External APIs return timestamps this has to survive: YouTube uses a
    trailing "Z", which `fromisoformat` rejects before Python 3.11, and some
    feeds provide no date at all. An unparseable date must not take down
    ranking for the whole batch, so it is treated as old rather than fatal.
    """
    from datetime import datetime

    if not published_at_iso:
        return _UNDATED_AGE_DAYS
    try:
        published = datetime.fromisoformat(published_at_iso.strip().replace("Z", "+00:00"))
    except ValueError:
        return _UNDATED_AGE_DAYS
    if published.tzinfo is None:
        published = published.replace(tzinfo=now.tzinfo)
    return max((now - published).total_seconds() / 86400, 0)


def compute_feedback_factor(feedback_history: list[dict], item: dict) -> float:
    """Boost items whose domain/type the user has previously responded well to."""
    if not feedback_history:
        return 0.5  # neutral prior — cold start
    positive = {"thumbs_up", "done", "save"}
    negative = {"thumbs_down", "not_for_me"}
    same_domain_signals = [f for f in feedback_history if f.get("domain") == item.get("domain")]
    if not same_domain_signals:
        return 0.5
    pos = sum(1 for f in same_domain_signals if f["interaction_type"] in positive)
    neg = sum(1 for f in same_domain_signals if f["interaction_type"] in negative)
    total = pos + neg
    if total == 0:
        return 0.5
    return pos / total


def compute_final_score(
    item: dict,
    user_vector: list[float],
    goal_vectors: list[list[float]],
    feedback_history: list[dict],
    safety_factor: float,
    now,
) -> dict:
    embedder = get_embedder()
    identity_match = embedder.similarity(item["embedding"], user_vector)
    goal_alignment = max((embedder.similarity(item["embedding"], gv) for gv in goal_vectors), default=0.0)
    growth_potential = item["growth_potential_score"]
    recency_score = 1 / (1 + math.log(max(1, days_since(item["published_at"], now))))
    feedback_factor = compute_feedback_factor(feedback_history, item)

    raw_score = (
        W_GOAL * goal_alignment
        + W_IDENTITY * identity_match
        + W_GROWTH * growth_potential
        + W_RECENCY * recency_score
        + W_FEEDBACK * feedback_factor
    )
    final_score = raw_score * safety_factor

    return {
        "final_score": final_score,
        "breakdown": {
            "goal_alignment": goal_alignment,
            "identity_match": identity_match,
            "growth_potential": growth_potential,
            "recency": recency_score,
            "feedback": feedback_factor,
        },
    }


def compute_confidence(interaction_count: int, profile_completeness: float, feedback_signal_quality: float) -> float:
    data_richness = min(interaction_count / 100, 1.0)
    return min(1.0, (data_richness + profile_completeness + feedback_signal_quality) / 3)
