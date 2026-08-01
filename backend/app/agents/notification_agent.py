"""Notification Agent (spec section 6.2.9). Builds the payload only —
actually delivering it (push/email/in-app) needs the desktop app / Chrome
extension proactivity tiers described in the spec, which are out of scope
this session.
"""

from app.agents.state import IABTMAgentState


def run(state: IABTMAgentState) -> tuple[dict, dict]:
    recs = state.get("ranked_recommendations", [])
    if not recs:
        payload = None
    else:
        top = recs[0]
        payload = {
            "title": "Your curator refreshed your feed",
            "body": f"Top pick: {top['title']} — {top['why_recommended']}",
            "deep_link": f"/media/{top['id']}",
        }

    updates = {"notification": payload}
    detail = {"generated": payload is not None}
    return updates, detail
