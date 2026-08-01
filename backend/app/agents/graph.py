"""LangGraph StateGraph wiring (spec section 7.2).

The Orchestrator Agent (spec 6.2.1) doesn't get its own node — in
LangGraph the graph *is* the orchestrator: it owns the routing rules the
orchestrator's system prompt describes (always identity+memory before
recommending, always safety before output, low confidence -> human
approval). That's expressed below as real conditional edges, not prose.
"""

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph

from app.agents import (
    content_retrieval_agent,
    evaluation_agent,
    goal_agent,
    human_approval_agent,
    identity_agent,
    memory_agent,
    notification_agent,
    output_agent,
    recommendation_agent,
    safety_agent,
)
from app.agents.state import IABTMAgentState
from app.agents.util import traced_node


def build_graph():
    workflow = StateGraph(IABTMAgentState)

    workflow.add_node("memory_load", traced_node("Memory Agent", memory_agent.run))
    workflow.add_node("identity_read", traced_node("Identity Agent", identity_agent.run))
    workflow.add_node("goal_fetch", traced_node("Goal Agent", goal_agent.run))
    workflow.add_node("content_retrieve", traced_node("Content Retrieval Agent", content_retrieval_agent.run))
    workflow.add_node("recommend", traced_node("Recommendation Agent", recommendation_agent.run))
    workflow.add_node("safety_check", traced_node("Safety Agent", safety_agent.run))
    workflow.add_node("evaluate", traced_node("Evaluation Agent", evaluation_agent.run))
    workflow.add_node("human_approval", traced_node("Human Approval", human_approval_agent.run))
    workflow.add_node("output", traced_node("Output", output_agent.run))
    workflow.add_node("notify", traced_node("Notification Agent", notification_agent.run))

    workflow.set_entry_point("memory_load")
    workflow.add_edge("memory_load", "identity_read")
    workflow.add_edge("identity_read", "goal_fetch")
    workflow.add_edge("goal_fetch", "content_retrieve")
    workflow.add_edge("content_retrieve", "recommend")
    workflow.add_edge("recommend", "safety_check")

    workflow.add_conditional_edges(
        "safety_check",
        lambda state: "evaluate" if state["safety_report"]["passed"] else "content_retrieve",
        {"evaluate": "evaluate", "content_retrieve": "content_retrieve"},
    )

    workflow.add_conditional_edges(
        "evaluate",
        lambda state: "human_approval" if state.get("needs_human_approval") else "output",
        {"human_approval": "human_approval", "output": "output"},
    )

    workflow.add_edge("human_approval", "output")
    workflow.add_edge("output", "notify")
    workflow.add_edge("notify", END)

    # Spec calls for PostgresSaver; a single-process prototype with SQLite
    # doesn't need a persistent external checkpoint store — InMemorySaver
    # gives the same checkpoint/thread_id/replay API, just not durable
    # across process restarts. Swap for PostgresSaver.from_conn_string(...)
    # when this needs to survive restarts.
    checkpointer = InMemorySaver()
    return workflow.compile(checkpointer=checkpointer)


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
