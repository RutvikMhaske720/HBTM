"""Pluggable vector store (spec section 10.3 calls for Qdrant collections).

`VectorStore` is the interface: upsert a vector + metadata under an id in a
named collection, similarity-search a collection, fetch or delete by id.
`LocalJSONVectorStore` is today's implementation — brute-force cosine
similarity over vectors kept in a local JSON file per collection, so this
runs with zero external services.

To move to a real vector DB later (Qdrant, Chroma, pgvector), write a new
class implementing the same four methods and swap it in `get_vector_store()`
below — no caller (semantic_search.py, agents, routers) needs to change.
"""

import json
import os
import threading
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np

from app.config import get_settings


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, collection: str, id: str, vector: list[float], metadata: dict | None = None) -> None: ...

    @abstractmethod
    def get(self, collection: str, id: str) -> dict | None: ...

    @abstractmethod
    def delete(self, collection: str, id: str) -> None: ...

    @abstractmethod
    def similarity_search(
        self, collection: str, query_vector: list[float], top_k: int = 10, filters: dict | None = None
    ) -> list[dict]: ...


class LocalJSONVectorStore(VectorStore):
    def __init__(self, base_dir: Path):
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _path(self, collection: str) -> Path:
        return self._base_dir / f"{collection}.json"

    def _read(self, collection: str) -> dict:
        path = self._path(collection)
        if not path.exists():
            return {}
        raw = path.read_text().strip()
        return json.loads(raw) if raw else {}

    def _write(self, collection: str, data: dict) -> None:
        path = self._path(collection)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data))
        os.replace(tmp, path)

    def upsert(self, collection: str, id: str, vector: list[float], metadata: dict | None = None) -> None:
        with self._lock:
            data = self._read(collection)
            data[id] = {"vector": vector, "metadata": metadata or {}}
            self._write(collection, data)

    def get(self, collection: str, id: str) -> dict | None:
        with self._lock:
            return self._read(collection).get(id)

    def delete(self, collection: str, id: str) -> None:
        with self._lock:
            data = self._read(collection)
            data.pop(id, None)
            self._write(collection, data)

    def similarity_search(
        self, collection: str, query_vector: list[float], top_k: int = 10, filters: dict | None = None
    ) -> list[dict]:
        with self._lock:
            data = self._read(collection)
        if not query_vector or not data:
            return []

        query = np.array(query_vector)
        scored = []
        for id, entry in data.items():
            vector = entry.get("vector") or []
            if not vector:
                continue
            metadata = entry.get("metadata", {})
            if filters and not all(metadata.get(k) == v for k, v in filters.items()):
                continue
            candidate = np.array(vector)
            size = min(len(query), len(candidate))
            if size == 0:
                continue
            q, c = query[:size], candidate[:size]
            denom = (np.linalg.norm(q) * np.linalg.norm(c)) or 1e-9
            score = float(np.dot(q, c) / denom)
            scored.append({"id": id, "score": score, "metadata": metadata})

        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[:top_k]


_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        settings = get_settings()
        _vector_store = LocalJSONVectorStore(Path(settings.data_dir) / "vectors")
    return _vector_store
