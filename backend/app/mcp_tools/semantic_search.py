"""MCP: Semantic Search Server (spec section 8.2.4).

Real implementation against the local TF-IDF/SVD embedder (see
app/embeddings/embedder.py) standing in for Qdrant/pgvector + OpenAI —
no vector DB or embedding API key needed for a corpus this size.
"""

from sqlalchemy.orm import Session

from app.db.models import ContentItem
from app.embeddings.embedder import get_embedder


def embed_text(text: str) -> list[float]:
    return get_embedder().embed_text(text)


def similarity_search(db: Session, query_vector: list[float], collection: str = "content_items", top_k: int = 20, filters: dict | None = None) -> list[dict]:
    embedder = get_embedder()
    query = db.query(ContentItem)
    filters = filters or {}
    if domain := filters.get("domain"):
        query = query.filter(ContentItem.domain == domain)
    items = query.all()
    scored = [(item, embedder.similarity(query_vector, item.embedding)) for item in items]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return [
        {
            "content_id": item.id,
            "title": item.title,
            "score": score,
        }
        for item, score in scored[:top_k]
    ]


def upsert_content_embedding(db: Session, content_id: str, text: str) -> None:
    item = db.get(ContentItem, content_id)
    if not item:
        return
    item.embedding = get_embedder().embed_text(text)
    db.commit()


def build_user_query_vector(identity_summary: str, goal_descriptions: list[str]) -> list[float]:
    embedder = get_embedder()
    return embedder.weighted_average(
        [
            (embedder.embed_text(identity_summary), 0.5),
            (embedder.embed_text(" ".join(goal_descriptions)), 0.5),
        ]
    )
