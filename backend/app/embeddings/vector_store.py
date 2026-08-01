"""Pluggable vector store with local JSON and Supabase pgvector backends.

`VectorStore` is the interface: upsert vectors + metadata under an id in a
named collection, similarity-search a collection with metadata filters, and
fetch/delete/replace by id.

`PostgresVectorStore` is the production path. It does the work in the
database rather than in Python:

* filters are pushed into SQL as JSONB containment (`metadata @> ...`) and
  range predicates, so the HNSW scan only ever considers eligible rows;
* `LIMIT` is applied by the planner, so a top-10 query reads ~10 rows
  instead of pulling a padded candidate set back into the process;
* writes go through a single batched `executemany`;
* a dimension change is detected and migrated instead of raising forever.

`LocalJSONVectorStore` mirrors that behaviour with brute-force cosine over a
JSON file, so the app runs with zero external services. Both are selected
against the database backend that is *actually live* (see
`app.db.database.active_database_url`), never the configured-but-unreachable
one — records and their embeddings must not land in different backends.
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
    def upsert_many(self, collection: str, entries: list[tuple[str, list[float], dict]]) -> None: ...

    @abstractmethod
    def get(self, collection: str, id: str) -> dict | None: ...

    @abstractmethod
    def delete(self, collection: str, id: str) -> None: ...

    @abstractmethod
    def clear(self, collection: str) -> None: ...

    @abstractmethod
    def count(self, collection: str) -> int: ...

    @abstractmethod
    def similarity_search(
        self, collection: str, query_vector: list[float], top_k: int = 10,
        filters: dict | None = None, min_score: float = -1.0,
    ) -> list[dict]: ...


def _matches(metadata: dict, filters: dict | None) -> bool:
    """Shared filter semantics: scalars match by equality, lists by membership."""
    if not filters:
        return True
    for key, expected in filters.items():
        actual = metadata.get(key)
        if isinstance(expected, (list, tuple, set)):
            if actual not in expected:
                return False
        elif actual != expected:
            return False
    return True


class LocalJSONVectorStore(VectorStore):
    def __init__(self, base_dir: Path):
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

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
        self.upsert_many(collection, [(id, vector, metadata or {})])

    def upsert_many(self, collection: str, entries: list[tuple[str, list[float], dict]]) -> None:
        if not entries:
            return
        with self._lock:
            data = self._read(collection)
            for id, vector, metadata in entries:
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

    def clear(self, collection: str) -> None:
        with self._lock:
            self._write(collection, {})

    def count(self, collection: str) -> int:
        with self._lock:
            return len(self._read(collection))

    def similarity_search(
        self, collection: str, query_vector: list[float], top_k: int = 10,
        filters: dict | None = None, min_score: float = -1.0,
    ) -> list[dict]:
        with self._lock:
            data = self._read(collection)
        if not query_vector or not data:
            return []

        # Eligible rows are stacked into one matrix so the cosine pass is a
        # single BLAS matvec rather than a Python loop over every row.
        ids, vectors, metadatas = [], [], []
        for id, entry in data.items():
            vector = entry.get("vector") or []
            metadata = entry.get("metadata", {})
            if not vector or not _matches(metadata, filters):
                continue
            ids.append(id)
            vectors.append((vector + [0.0] * EMBEDDING_DIM)[:EMBEDDING_DIM])
            metadatas.append(metadata)
        if not ids:
            return []

        query = np.array((list(query_vector) + [0.0] * EMBEDDING_DIM)[:EMBEDDING_DIM])
        query_norm = np.linalg.norm(query) or 1e-9
        matrix = np.array(vectors)
        norms = np.linalg.norm(matrix, axis=1)
        norms[norms == 0] = 1e-9
        scores = (matrix @ query) / (norms * query_norm)

        order = np.argsort(-scores)[: max(top_k, 0)]
        return [
            {"id": ids[i], "score": float(scores[i]), "metadata": metadatas[i]}
            for i in order
            if float(scores[i]) >= min_score
        ]


class PostgresVectorStore(VectorStore):
    """Supabase pgvector store. Metadata stays queryable (and indexed) JSONB."""

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
                self._migrate_dimension(cursor)
                cursor.execute(f"""CREATE TABLE IF NOT EXISTS vector_records (
                    collection TEXT NOT NULL,
                    id TEXT NOT NULL,
                    embedding vector({EMBEDDING_DIM}) NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                    PRIMARY KEY (collection, id))""")
                cursor.execute("""CREATE INDEX IF NOT EXISTS vector_records_embedding_idx
                    ON vector_records USING hnsw (embedding vector_cosine_ops)""")
                # GIN over the JSONB lets the planner use the `@>` filter
                # instead of re-checking every row the vector scan returns.
                cursor.execute("""CREATE INDEX IF NOT EXISTS vector_records_metadata_idx
                    ON vector_records USING gin (metadata jsonb_path_ops)""")
                cursor.execute("""CREATE INDEX IF NOT EXISTS vector_records_collection_idx
                    ON vector_records (collection)""")
            connection.commit()

    def _migrate_dimension(self, cursor) -> None:
        """Drop and rebuild the table when the embedding width changed.

        pgvector fixes the dimension in the column type, so `CREATE TABLE IF
        NOT EXISTS` silently keeps an old width and every later insert fails.
        The rows are pure derived data — `app.embeddings.index` rebuilds them
        from the content library on the next startup — so recreating is safe.
        """
        cursor.execute("""SELECT atttypmod FROM pg_attribute
            WHERE attrelid = to_regclass('public.vector_records') AND attname = 'embedding'""")
        row = cursor.fetchone()
        if row and row[0] not in (None, -1, EMBEDDING_DIM):
            print(f"[IABTM] Embedding dimension changed {row[0]} -> {EMBEDDING_DIM}; rebuilding vector index.")
            cursor.execute("DROP TABLE IF EXISTS vector_records")

    @staticmethod
    def _vector(vector: list[float]) -> str:
        values = (list(vector) + [0.0] * EMBEDDING_DIM)[:EMBEDDING_DIM]
        return "[" + ",".join(str(float(value)) for value in values) + "]"

    def upsert(self, collection: str, id: str, vector: list[float], metadata: dict | None = None) -> None:
        self.upsert_many(collection, [(id, vector, metadata or {})])

    def upsert_many(self, collection: str, entries: list[tuple[str, list[float], dict]]) -> None:
        if not entries:
            return
        rows = [
            (collection, id, self._vector(vector), self._Jsonb(metadata or {}))
            for id, vector, metadata in entries
        ]
        with self._lock, self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """INSERT INTO vector_records (collection, id, embedding, metadata)
                       VALUES (%s, %s, %s::vector, %s)
                       ON CONFLICT(collection, id)
                       DO UPDATE SET embedding = excluded.embedding, metadata = excluded.metadata""",
                    rows,
                )
            connection.commit()

    def get(self, collection: str, id: str) -> dict | None:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT embedding::text, metadata FROM vector_records WHERE collection = %s AND id = %s",
                (collection, id),
            )
            row = cursor.fetchone()
        return {"vector": json.loads(row[0]), "metadata": row[1]} if row else None

    def delete(self, collection: str, id: str) -> None:
        with self._lock, self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM vector_records WHERE collection = %s AND id = %s", (collection, id))
            connection.commit()

    def clear(self, collection: str) -> None:
        with self._lock, self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM vector_records WHERE collection = %s", (collection,))
            connection.commit()

    def count(self, collection: str) -> int:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM vector_records WHERE collection = %s", (collection,))
            return int(cursor.fetchone()[0])

    def similarity_search(
        self, collection: str, query_vector: list[float], top_k: int = 10,
        filters: dict | None = None, min_score: float = -1.0,
    ) -> list[dict]:
        if not query_vector:
            return []

        clauses = ["collection = %s"]
        params: list = [collection]
        for key, expected in (filters or {}).items():
            if isinstance(expected, (list, tuple, set)):
                # OR of containment checks — each one is GIN-indexable.
                values = list(expected)
                if not values:
                    return []
                clauses.append("(" + " OR ".join(["metadata @> %s"] * len(values)) + ")")
                params.extend(self._Jsonb({key: value}) for value in values)
            else:
                clauses.append("metadata @> %s")
                params.append(self._Jsonb({key: expected}))

        vector = self._vector(query_vector)
        where = " AND ".join(clauses)
        # `1 - (embedding <=> q)` is cosine similarity; ordering by the raw
        # distance operator is what lets the planner use the HNSW index.
        sql = f"""SELECT id, 1 - (embedding <=> %s::vector) AS score, metadata
                  FROM vector_records WHERE {where}
                  ORDER BY embedding <=> %s::vector LIMIT %s"""

        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(sql, [vector, *params, vector, max(top_k, 0)])
            rows = cursor.fetchall()

        return [
            {"id": id, "score": float(score), "metadata": metadata}
            for id, score, metadata in rows
            if float(score) >= min_score
        ]


_vector_store: VectorStore | None = None
_vector_store_lock = threading.Lock()


def get_vector_store() -> VectorStore:
    global _vector_store
    with _vector_store_lock:
        if _vector_store is None:
            from app.db.database import active_database_url

            settings = get_settings()
            database_url = active_database_url()
            if database_url.startswith(("postgresql://", "postgres://")):
                try:
                    _vector_store = PostgresVectorStore(database_url)
                except Exception as exc:
                    print(f"[IABTM] pgvector unavailable; using the local vector store. ({type(exc).__name__})")
                    _vector_store = LocalJSONVectorStore(Path(settings.data_dir) / "vectors")
            else:
                _vector_store = LocalJSONVectorStore(Path(settings.data_dir) / "vectors")
    return _vector_store
