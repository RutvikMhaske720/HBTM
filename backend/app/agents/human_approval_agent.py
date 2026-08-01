"""Human-in-the-loop node (spec section 7.2 `human_approval`, interrupt_before).

A true implementation would call LangGraph's `interrupt()` here and the
API layer would resume the thread with `Command(resume=...)` once the
user answers a clarifying question in the UI — that requires a UI
surface for the prompt, which doesn't exist yet this session. This node
is a faithful placeholder: the conditional edge that routes low-confidence
runs here is real and working, it just auto-approves for now instead of
pausing. Swapping in a real pause/resume is a same-file change once the
frontend has somewhere to render the question.
"""

from app.agents.state import IABTMAgentState


def run(state: IABTMAgentState) -> tuple[dict, dict]:
    detail = {
        "auto_approved": True,
        "reason": "confidence below threshold, but no human-in-the-loop UI wired this session",
        "confidence_score": state.get("confidence_score"),
    }
    return {}, detail
