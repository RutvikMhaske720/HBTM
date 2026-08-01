"""Pluggable vector store with local JSON and production pgvector backends.

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
from app.embeddings.embedder import EMBEDDING_DIM


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


class PostgresVectorStore(VectorStore):
    """Supabase pgvector store. Metadata remains queryable JSONB."""

    def __init__(self, database_url: str):
        import psycopg
        from psycopg.types.json import Jsonb

        self._psycopg = psycopg
        self._Jsonb = Jsonb
        self._database_url = database_url
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self):
        return self._psycopg.connect(self._database_url, connect_timeout=10)

    def _initialize(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                cursor.execute(f"""CREATE TABLE IF NOT EXISTS vector_records (
                    collection TEXT NOT NULL,
                    id TEXT NOT NULL,
                    embedding vector({EMBEDDING_DIM}) NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                    PRIMARY KEY (collection, id))""")
                cursor.execute("""CREATE INDEX IF NOT EXISTS vector_records_embedding_idx
                    ON vector_records USING hnsw (embedding vector_cosine_ops)""")

    @staticmethod
    def _vector(vector: list[float]) -> str:
        values = (vector + [0.0] * EMBEDDING_DIM)[:EMBEDDING_DIM]
        return "[" + ",".join(str(float(value)) for value in values) + "]"

    def upsert(self, collection: str, id: str, vector: list[float], metadata: dict | None = None) -> None:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("""INSERT INTO vector_records (collection, id, embedding, metadata)
                VALUES (%s, %s, %s::vector, %s)
                ON CONFLICT(collection, id) DO UPDATE SET embedding = excluded.embedding, metadata = excluded.metadata""",
                (collection, id, self._vector(vector), self._Jsonb(metadata or {})))

    def get(self, collection: str, id: str) -> dict | None:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT embedding::text, metadata FROM vector_records WHERE collection = %s AND id = %s", (collection, id))
            row = cursor.fetchone()
        return {"vector": json.loads(row[0]), "metadata": row[1]} if row else None

    def delete(self, collection: str, id: str) -> None:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("DELETE FROM vector_records WHERE collection = %s AND id = %s", (collection, id))

    def similarity_search(self, collection: str, query_vector: list[float], top_k: int = 10, filters: dict | None = None) -> list[dict]:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("""SELECT id, 1 - (embedding <=> %s::vector) AS score, metadata
                FROM vector_records WHERE collection = %s
                ORDER BY embedding <=> %s::vector LIMIT %s""",
                (self._vector(query_vector), collection, self._vector(query_vector), top_k * 3))
            rows = cursor.fetchall()
        results = []
        for id, score, metadata in rows:
            if filters and not all(metadata.get(key) == value for key, value in filters.items()):
                continue
            results.append({"id": id, "score": float(score), "metadata": metadata})
            if len(results) == top_k:
                break
        return results


_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        settings = get_settings()
        if settings.database_url.startswith(("postgresql://", "postgres://")):
            _vector_store = PostgresVectorStore(settings.database_url)
        else:
            _vector_store = LocalJSONVectorStore(Path(settings.data_dir) / "vectors")
    return _vector_store
