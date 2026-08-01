"""MCP: Reddit Server (spec section 8.2.2). Mocked — no PRAW app credentials
were provided this session. Real calls would use `praw.Reddit(client_id=...,
client_secret=..., user_agent=...)`; swap the bodies below for real PRAW
calls once `settings.reddit_mocked` is False.
"""

import hashlib

from app.config import get_settings

_DOMAIN_SUBREDDITS = {
    "Mindset": ["r/getdisciplined", "r/DecidingToBeBetter"],
    "Creativity": ["r/ArtistLounge", "r/writing"],
    "Health": ["r/Fitness", "r/loseit"],
    "Finance": ["r/personalfinance", "r/financialindependence"],
    "Career": ["r/careerguidance", "r/cscareerquestions"],
    "Relationships": ["r/relationship_advice"],
    "Knowledge": ["r/todayilearned"],
    "Purpose": ["r/DecidingToBeBetter"],
}


def search_subreddits(query: str, growth_domain: str | None = None) -> list[dict]:
    settings = get_settings()
    if not settings.reddit_mocked:
        raise NotImplementedError("Real Reddit integration not wired in this session — no app credentials provided.")
    subs = _DOMAIN_SUBREDDITS.get(growth_domain or "", ["r/DecidingToBeBetter"])
    return [{"subreddit": s, "description": f"Mocked community result for '{query}'"} for s in subs]


def get_top_posts(subreddit: str, time_filter: str = "week", limit: int = 5) -> list[dict]:
    settings = get_settings()
    if not settings.reddit_mocked:
        raise NotImplementedError("Real Reddit integration not wired in this session — no app credentials provided.")
    posts = []
    for i in range(limit):
        seed = f"{subreddit}-{time_filter}-{i}"
        posts.append(
            {
                "post_id": hashlib.sha1(seed.encode()).hexdigest()[:8],
                "title": f"Mocked top post #{i + 1} in {subreddit}",
                "score": 1000 - i * 120,
                "num_comments": 80 - i * 8,
                "subreddit": subreddit,
            }
        )
    return posts


def get_post_with_comments(post_id: str, comment_depth: int = 2) -> dict:
    return {"post_id": post_id, "title": "Mocked post", "top_comments": []}


def search_posts(query: str, subreddits: list[str], time_filter: str = "month") -> list[dict]:
    return [{"post_id": hashlib.sha1(f"{query}{s}".encode()).hexdigest()[:8], "title": f"Mocked result for '{query}' in {s}", "subreddit": s} for s in subreddits]


def get_user_activity(username: str, limit: int = 10) -> list[dict]:
    return []
