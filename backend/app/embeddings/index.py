"""Keeps the vector index consistent with the content library.

The embedder is fit-free and deterministic (see `app.embeddings.embedder`),
so a vector written today is still comparable to one written months ago and
the index never silently goes stale. That leaves this module with two jobs:

* fill in vectors for records that don't have one yet;
* rebuild everything when the embedding scheme itself changes, which is
  detected by storing `EMBEDDING_VERSION` alongside each vector.
"""

import threading

from app.db.database import Store
from app.embeddings.embedder import EMBEDDING_VERSION, get_embedder
from app.embeddings.vector_store import get_vector_store

CONTENT_COLLECTION = "content_items"
PROFILE_COLLECTION = "user_profiles"

_lock = threading.RLock()


def content_text(item: dict) -> str:
    """The single text representation used for both indexing and querying."""
    parts = [
        item.get("title", ""),
        item.get("description", ""),
        item.get("domain", ""),
        item.get("content_type", ""),
    ]
    return " ".join(part for part in parts if part).strip()


def content_metadata(item: dict) -> dict:
    """Filterable facets kept alongside the vector.

    These are duplicated out of the record on purpose: it lets the database
    apply `domain` / `content_type` / `has_preview` predicates during the
    index scan instead of returning rows the caller has to throw away.
    """
    return {
        "domain": item.get("domain", ""),
        "content_type": item.get("content_type", ""),
        "source": item.get("source", ""),
        "published_at": item.get("published_at", ""),
        "has_preview": bool(item.get("thumbnail_url") or item.get("video_id")),
        "v": EMBEDDING_VERSION,
    }


def ensure_index(db: Store, force: bool = False) -> dict:
    """Bring the index in line with the library.

    Returns a small report so callers (startup, ingestion) can log what
    happened without inspecting internals.
    """
    with _lock:
        items = list(db.content_items.all())
        vector_store = get_vector_store()

        if force or _scheme_changed(vector_store, items):
            vector_store.clear(CONTENT_COLLECTION)
            vector_store.clear(PROFILE_COLLECTION)
            _write(db, items)
            return {"rebuilt": True, "reindexed": len(items), "library_size": len(items)}

        missing = [item for item in items if vector_store.get(CONTENT_COLLECTION, item["id"]) is None]
        _write(db, missing)
        return {"rebuilt": False, "reindexed": len(missing), "library_size": len(items)}


def _scheme_changed(vector_store, items: list[dict]) -> bool:
    """True when stored vectors came from a different embedding scheme."""
    for item in items[:5]:  # a sample is enough; the whole index is written together
        entry = vector_store.get(CONTENT_COLLECTION, item["id"])
        if entry and entry.get("metadata", {}).get("v") != EMBEDDING_VERSION:
            return True
    return False


def _write(db: Store, items: list[dict]) -> None:
    """Embed a batch and persist it to both the record store and the index."""
    if not items:
        return
    embeddings = get_embedder().embed_many([content_text(item) for item in items])
    entries = []
    for item, embedding in zip(items, embeddings):
        item["embedding"] = embedding
        db.content_items.upsert(item)
        entries.append((item["id"], embedding, content_metadata(item)))
    get_vector_store().upsert_many(CONTENT_COLLECTION, entries)


def index_items(db: Store, items: list[dict]) -> None:
    """Index freshly ingested items."""
    with _lock:
        _write(db, items)
