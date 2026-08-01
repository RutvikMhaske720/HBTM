"""MCP: Web Search Server (spec section 8.2.5). Mocked — no Tavily/Brave key
was provided this session. Real calls would POST to the chosen provider's
search endpoint with `settings.web_search_api_key`.
"""

import hashlib

from app.config import get_settings


def web_search(query: str, max_results: int = 5, include_raw: bool = False) -> list[dict]:
    settings = get_settings()
    if not settings.web_search_mocked:
        raise NotImplementedError("Real web search integration not wired in this session — no API key provided.")
    return [
        {
            "url": f"https://example-growth-editorial.test/{hashlib.sha1(f'{query}{i}'.encode()).hexdigest()[:10]}",
            "title": f"Mocked web result #{i + 1} for '{query}'",
            "snippet": f"A mocked search snippet standing in for a real web result about '{query}'.",
        }
        for i in range(max_results)
    ]


def extract_article(url: str) -> str:
    return f"[mocked extracted article text for {url}]"
