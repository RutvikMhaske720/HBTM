"""MCP: Semantic Search Server (spec section 8.2.4).

Real implementation against the local TF-IDF/SVD embedder (see
app/embeddings/embedder.py) standing in for OpenAI text-embedding-3-small,
paired with the local `VectorStore` (see app/embeddings/vector_store.py)
standing in for Qdrant/pgvector — same upsert/similarity_search interface a
hosted vector DB exposes, so swapping one in later doesn't touch any caller.
"""

from app.db.database import Store
from app.embeddings.embedder import get_embedder
from app.embeddings.vector_store import get_vector_store

CONTENT_COLLECTION = "content_items"


def embed_text(text: str) -> list[float]:
    return get_embedder().embed_text(text)


def similarity_search(
    db: Store, query_vector: list[float], collection: str = CONTENT_COLLECTION, top_k: int = 20,
    filters: dict | None = None,
) -> list[dict]:
    hits = get_vector_store().similarity_search(collection, query_vector, top_k=top_k, filters=filters)
    results = []
    for hit in hits:
        item = db.content_items.get(hit["id"])
        if not item:
            continue
        results.append({"content_id": item["id"], "title": item["title"], "score": hit["score"]})
    return results


def upsert_content_embedding(db: Store, content_id: str, text: str) -> None:
    item = db.content_items.get(content_id)
    if not item:
        return
    embedding = get_embedder().embed_text(text)
    item["embedding"] = embedding
    db.content_items.upsert(item)
    get_vector_store().upsert(
        CONTENT_COLLECTION, content_id, embedding,
        {"domain": item["domain"], "content_type": item["content_type"]},
    )


def build_user_query_vector(identity_summary: str, goal_descriptions: list[str]) -> list[float]:
    embedder = get_embedder()
    return embedder.weighted_average(
        [
            (embedder.embed_text(identity_summary), 0.5),
            (embedder.embed_text(" ".join(goal_descriptions)), 0.5),
        ]
    )
