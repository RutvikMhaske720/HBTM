"""MCP: Activity Tracker Server (spec section 8.2.7). Mocked — this session
has no Chrome Extension or Desktop App emitting real events, so this
always returns empty activity. Real implementation would read from a local
Redis stream fed by the extension/desktop watcher.
"""


def get_recent_activity(user_id: str, time_range_hours: int = 24) -> list[dict]:
    return []


def register_trigger(trigger_rule: dict) -> str:
    return "mock-trigger-id"


def get_trigger_events(user_id: str, since: str | None = None) -> list[dict]:
    return []
