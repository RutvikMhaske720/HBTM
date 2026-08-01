"""Identity Agent (spec section 6.2.2).

Builds a compressed natural-language identity context summary from the
Identity Graph. No LLM call is used here (no model API key was provided
this session) — the summary is templated deterministically from the
graph's current-self / imagined-self nodes, weighted by their `weight`
field so future behavior-inferred boosts naturally surface stronger.
"""

from app.agents.state import IABTMAgentState
from app.db.database import SessionLocal
from app.mcp_tools import internal_db


def run(state: IABTMAgentState) -> tuple[dict, dict]:
    user_id = state["user_id"]
    with SessionLocal() as db:
        graph = internal_db.get_identity_graph(db, user_id)

    current = sorted(
        (n for n in graph["nodes"] if n["polarity"] == "current"),
        key=lambda n: n["weight"],
        reverse=True,
    )
    imagined = sorted(
        (n for n in graph["nodes"] if n["polarity"] == "imagined"),
        key=lambda n: n["weight"],
        reverse=True,
    )

    current_labels = [n["label"] for n in current]
    imagined_labels = [n["label"] for n in imagined]

    if current_labels or imagined_labels:
        summary = (
            f"Current self is shaped by: {', '.join(current_labels) or 'no declared traits yet'}. "
            f"Imagined self reaches toward: {', '.join(imagined_labels) or 'no declared aspirations yet'}. "
            f"The gap between '{current_labels[0]}' and '{imagined_labels[0]}' is the primary growth vector."
            if current_labels and imagined_labels
            else f"Current self: {', '.join(current_labels)}. Imagined self: {', '.join(imagined_labels)}."
        )
    else:
        summary = "No identity signal yet — cold start, relying on goal domains and archetype defaults."

    updates = {"identity_summary": summary}
    detail = {"node_count": len(graph["nodes"]), "current_traits": len(current), "imagined_traits": len(imagined)}
    return updates, detail
