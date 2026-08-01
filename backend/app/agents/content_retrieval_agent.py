"""Content Retrieval Agent (spec section 6.2.6).

Pulls candidates from the internal library plus the (mocked) external
MCP sources, normalizing everything into one shape so the Recommendation
Agent can score internal and external items identically.
"""

import hashlib
from datetime import datetime, timezone

from app.agents.state import IABTMAgentState
from app.db.database import SessionLocal
from app.mcp_tools import internal_db, reddit, semantic_search, youtube

MAX_CANDIDATES = 60


def _external_to_candidate(title: str, description: str, domain: str, content_type: str, source: str, duration_minutes: int) -> dict:
    content_id = f"ext-{hashlib.sha1(f'{source}-{title}'.encode()).hexdigest()[:12]}"
    return {
        "id": content_id,
        "title": title,
        "content_type": content_type,
        "domain": domain,
        "description": description,
        "growth_potential_score": 0.6,  # unvetted external content — moderate default, Safety Agent still checks it
        "difficulty": "accessible",
        "duration_minutes": duration_minutes,
        "mood": "curious",
        "source": source,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "embedding": semantic_search.embed_text(f"{title} {description}"),
    }


def run(state: IABTMAgentState) -> tuple[dict, dict]:
    goals = state.get("active_goals", [])
    seen_ids = {f["content_id"] for f in state.get("feedback_history", [])}
    domains = [g["domain"] for g in goals] or ["Mindset", "Creativity", "Health"]

    candidates: dict[str, dict] = {}

    with SessionLocal() as db:
        for domain in domains:
            for item in internal_db.search_content_library(db, {"domain": domain, "exclude_ids": list(seen_ids)}):
                candidates[item["id"]] = item

        if len(candidates) < 20:
            for item in internal_db.search_content_library(db, {"exclude_ids": list(seen_ids)}):
                candidates.setdefault(item["id"], item)

    sources_used = {"internal": len(candidates)}

    for domain in domains[:3]:
        for video in youtube.search_youtube_videos(query=domain, category=domain, max_results=2):
            cand = _external_to_candidate(video["title"], video["description"], domain, "Film", "youtube", video["duration_seconds"] // 60)
            candidates[cand["id"]] = cand
        for post in reddit.get_top_posts(f"r/{domain}", limit=1):
            cand = _external_to_candidate(post["title"], f"Community discussion in {post['subreddit']}", domain, "Editorial", "reddit", 5)
            candidates[cand["id"]] = cand

    sources_used["youtube"] = sum(1 for c in candidates.values() if c["source"] == "youtube")
    sources_used["reddit"] = sum(1 for c in candidates.values() if c["source"] == "reddit")

    pool = list(candidates.values())[:MAX_CANDIDATES]
    updates = {"candidate_pool": pool}
    detail = {"candidate_count": len(pool), "sources": sources_used, "domains_queried": domains}
    return updates, detail
