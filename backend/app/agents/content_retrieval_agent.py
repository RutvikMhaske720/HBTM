"""Content Retrieval Agent (spec section 6.2.6).

Builds the candidate pool the Recommendation Agent ranks. Retrieval is
vector-first: the profile vector is the query, and the vector database
returns its nearest neighbours with the domain / preview filters already
applied inside the index scan. That replaces the previous approach of
loading the whole library and filtering it in Python — it scales, and more
importantly it retrieves by *meaning* rather than by exact domain match, so a
finance-flavoured mindset piece can still surface for a mindset goal.

When the index can't supply enough distinct, previewable candidates, the
agent curates live from the external sources instead of padding the pool with
weaker material.
"""

from app.agents.state import IABTMAgentState
from app.config import get_settings
from app.curation import pipeline
from app.curation.profile import build_profile
from app.db.database import SessionLocal
from app.embeddings.index import CONTENT_COLLECTION, content_text
from app.mcp_tools import semantic_search

MAX_CANDIDATES = 60
MIN_CANDIDATES = 18
# Media the live top-up will try, in the order it tries them.
TOPUP_TYPES = ["Videos", "Editorial", "Music"]


def run(state: IABTMAgentState) -> tuple[dict, dict]:
    settings = get_settings()
    user_id = state["user_id"]
    seen_ids = {event["content_id"] for event in state.get("feedback_history", [])}

    with SessionLocal() as db:
        profile = build_profile(db, user_id)
        # The graph's identity summary is richer than the one rebuilt here, so
        # prefer it and re-derive the query vector from it when present.
        identity_summary = state.get("identity_summary") or profile.identity_summary
        goals = state.get("active_goals", []) or profile.goals
        query_vector = semantic_search.build_user_query_vector(
            identity_summary,
            [f"{goal['domain']} {goal['title']}" for goal in goals] or ["personal growth"],
            db=db, feedback_history=state.get("feedback_history", []),
        ) or profile.vector

        candidates: dict[str, dict] = {}

        # Pass 1 — nearest neighbours across the whole library, previewable only.
        for hit in semantic_search.similarity_search(
            db, query_vector, collection=CONTENT_COLLECTION, top_k=MAX_CANDIDATES * 2,
            filters={"has_preview": True},
        ):
            if hit["id"] not in seen_ids:
                candidates[hit["id"]] = hit

        # Pass 2 — guarantee each goal domain is represented, so a single
        # dominant domain can't crowd the others out of the pool.
        for domain in profile.domains[:4]:
            for hit in semantic_search.similarity_search(
                db, query_vector, collection=CONTENT_COLLECTION, top_k=8,
                filters={"domain": domain, "has_preview": True},
            ):
                if hit["id"] not in seen_ids:
                    candidates.setdefault(hit["id"], hit)

        sources_used = {"vector_index": len(candidates)}
        topup_reports = []

        # Pass 3 — the index is thin for this user; go get real material.
        if len(candidates) < MIN_CANDIDATES:
            for content_type in TOPUP_TYPES:
                for domain in profile.domains[:2]:
                    items, report = pipeline.curate(
                        db, profile, content_type, domain, limit=6
                    )
                    topup_reports.append(report)
                    for item in items:
                        if item["id"] not in seen_ids:
                            candidates.setdefault(item["id"], dict(item))
                if len(candidates) >= MIN_CANDIDATES:
                    break
            sources_used["live_curation"] = len(candidates) - sources_used["vector_index"]

    pool = []
    for item in list(candidates.values())[:MAX_CANDIDATES]:
        # The scorer needs an embedding on every candidate; live-curated items
        # were just indexed, so this only fills gaps from legacy records.
        if not item.get("embedding"):
            item["embedding"] = semantic_search.embed_text(content_text(item))
        pool.append(item)

    updates = {"candidate_pool": pool}
    detail = {
        "candidate_count": len(pool),
        "sources": sources_used,
        "domains_queried": profile.domains,
        "relevance_threshold": settings.curation_relevance_threshold,
        "live_topups": topup_reports,
    }
    return updates, detail
