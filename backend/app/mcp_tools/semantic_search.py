"""MCP: Semantic Search Server (spec section 8.2.4).

Thin, caller-facing surface over the embedder (`app.embeddings.embedder`) and
the vector database (`app.embeddings.vector_store`). Everything that ranks or
filters content semantically goes through here, so there is exactly one place
that knows how a query vector is built and how the index is queried.

The user query vector blends three signals, in descending weight:

* **goals** — what they said they're working toward;
* **identity** — the current-self / imagined-self graph plus free-text notes;
* **taste** — the centroid of items they've actually responded well to.

The taste term is what makes the vector database do real work: positive
feedback moves the query point inside the same space the catalogue lives in,
so the next retrieval leans toward that neighbourhood without any
hand-written rules about domains or content types.
"""

from app.db.database import Store
from app.embeddings.embedder import get_embedder
from app.embeddings.index import (
    CONTENT_COLLECTION,
    PROFILE_COLLECTION,
    content_metadata,
    content_text,
)
from app.embeddings.vector_store import get_vector_store

POSITIVE_SIGNALS = {"thumbs_up", "done", "save"}
NEGATIVE_SIGNALS = {"thumbs_down", "not_for_me"}

W_GOALS, W_IDENTITY, W_TASTE = 0.45, 0.30, 0.25


def embed_text(text: str) -> list[float]:
    return get_embedder().embed_text(text)


def embed_many(texts: list[str]) -> list[list[float]]:
    return get_embedder().embed_many(texts)


def similarity_search(
    db: Store, query_vector: list[float], collection: str = CONTENT_COLLECTION, top_k: int = 20,
    filters: dict | None = None, min_score: float = -1.0,
) -> list[dict]:
    """Nearest neighbours, hydrated with the records they point at.

    `filters` is applied inside the database, so `top_k` is the number of
    eligible rows read — not a candidate set trimmed afterwards in Python.
    """
    hits = get_vector_store().similarity_search(
        collection, query_vector, top_k=top_k, filters=filters, min_score=min_score
    )
    results = []
    for hit in hits:
        item = db.content_items.get(hit["id"])
        if not item:
            continue
        results.append({**item, "score": hit["score"]})
    return results


def find_duplicates(query_vector: list[float], threshold: float, top_k: int = 3) -> list[dict]:
    """Existing items close enough to `query_vector` to count as the same thing."""
    return get_vector_store().similarity_search(
        CONTENT_COLLECTION, query_vector, top_k=top_k, min_score=threshold
    )


def upsert_content_embedding(db: Store, content_id: str, text: str = "") -> None:
    item = db.content_items.get(content_id)
    if not item:
        return
    embedding = get_embedder().embed_text(text or content_text(item))
    item["embedding"] = embedding
    db.content_items.upsert(item)
    get_vector_store().upsert(CONTENT_COLLECTION, content_id, embedding, content_metadata(item))


def taste_vector(db: Store, feedback_history: list[dict]) -> list[float]:
    """Centroid of what the user liked, minus what they rejected.

    Vectors are read straight from the index rather than re-embedded, so this
    stays a couple of key lookups regardless of history length.
    """
    if not feedback_history:
        return []
    vector_store = get_vector_store()
    liked, disliked = [], []
    for event in feedback_history:
        signal = event.get("interaction_type")
        if signal not in POSITIVE_SIGNALS and signal not in NEGATIVE_SIGNALS:
            continue
        entry = vector_store.get(CONTENT_COLLECTION, event.get("content_id", ""))
        if not entry or not entry.get("vector"):
            continue
        (liked if signal in POSITIVE_SIGNALS else disliked).append(entry["vector"])

    if not liked:
        return []
    embedder = get_embedder()
    weighted = [(vector, 1.0 / len(liked)) for vector in liked]
    # Rejections push the query point away, but never far enough to invert it.
    weighted += [(vector, -0.4 / len(disliked)) for vector in disliked]
    return embedder.weighted_average(weighted)


def build_user_query_vector(
    identity_summary: str, goal_descriptions: list[str],
    db: Store | None = None, feedback_history: list[dict] | None = None,
) -> list[float]:
    embedder = get_embedder()
    components = [
        (embedder.embed_text(" ".join(goal_descriptions)), W_GOALS),
        (embedder.embed_text(identity_summary), W_IDENTITY),
    ]
    if db is not None and feedback_history:
        taste = taste_vector(db, feedback_history)
        if taste:
            components.append((taste, W_TASTE))
    return embedder.weighted_average(components)


def save_user_vector(user_id: str, vector: list[float], metadata: dict | None = None) -> None:
    """Persist a profile vector so retrieval and 'more like this' agree."""
    if vector:
        get_vector_store().upsert(PROFILE_COLLECTION, user_id, vector, metadata or {})


def load_user_vector(user_id: str) -> list[float]:
    entry = get_vector_store().get(PROFILE_COLLECTION, user_id)
    return entry.get("vector", []) if entry else []
