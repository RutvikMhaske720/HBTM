"""Persistence repository backed by SQLite locally or PostgreSQL in Supabase.

The application uses the same collection-shaped API in both environments.
PostgreSQL stores JSONB records atomically and is the production source of
truth; pgvector lives alongside it in ``app.embeddings.vector_store``.
"""

import json
import sqlite3
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.config import get_settings


class Record(dict):
    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value) -> None:
        self[name] = value


class Result:
    def __init__(self, rows: list[Any]):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class Collection:
    def __init__(self, store: "BaseStore", name: str):
        self._store = store
        self._name = name

    @staticmethod
    def _record(payload: Any) -> Record:
        return Record(payload if isinstance(payload, dict) else json.loads(payload))

    def get(self, id: str) -> Record | None:
        row = self._store._execute(
            f"SELECT payload FROM records WHERE collection = {self._store.p} AND id = {self._store.p}",
            (self._name, id),
        ).fetchone()
        return self._record(row[0]) if row else None

    def all(self) -> list[Record]:
        order = "created_at" if self._store.is_postgres else "rowid"
        rows = self._store._execute(
            f"SELECT payload FROM records WHERE collection = {self._store.p} ORDER BY {order}", (self._name,)
        ).fetchall()
        return [self._record(row[0]) for row in rows]

    def filter(self, predicate: Callable[[dict], bool]) -> list[Record]:
        return [record for record in self.all() if predicate(record)]

    def count(self) -> int:
        row = self._store._execute(
            f"SELECT COUNT(*) FROM records WHERE collection = {self._store.p}", (self._name,)
        ).fetchone()
        return int(row[0])

    def upsert(self, record: dict) -> Record:
        saved = dict(record)
        if not saved.get("id"):
            raise ValueError("Records must have an id")
        self._store._execute(
            f"""INSERT INTO records (collection, id, payload) VALUES ({self._store.p}, {self._store.p}, {self._store.p})
                ON CONFLICT(collection, id) DO UPDATE SET payload = excluded.payload""",
            (self._name, saved["id"], self._store.payload(saved)),
            commit=True,
        )
        return Record(saved)

    def delete(self, id: str) -> None:
        self._store._execute(
            f"DELETE FROM records WHERE collection = {self._store.p} AND id = {self._store.p}",
            (self._name, id), commit=True,
        )


class BaseStore:
    collection_names = (
        "users", "identity_nodes", "goals", "content_items", "interaction_events",
        "agent_runs", "agent_step_logs",
    )
    p = "?"
    is_postgres = False

    def _set_collections(self) -> None:
        for name in self.collection_names:
            setattr(self, name, Collection(self, name))

    def __enter__(self):
        return self

    def __exit__(self, *exc_info) -> None:
        return None


class SQLiteStore(BaseStore):
    def __init__(self, database_path: Path):
        self.database_path = database_path
        self._lock = threading.RLock()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()
        self._set_collections()
        self._migrate_legacy_json(database_path.parent)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS records (
                collection TEXT NOT NULL, id TEXT NOT NULL, payload TEXT NOT NULL,
                PRIMARY KEY (collection, id))""")
            connection.execute("CREATE INDEX IF NOT EXISTS records_collection_idx ON records (collection)")

    def _migrate_legacy_json(self, legacy_dir: Path) -> None:
        for name in self.collection_names:
            source = legacy_dir / f"{name}.json"
            collection = getattr(self, name)
            if collection.count() or not source.exists():
                continue
            try:
                records = json.loads(source.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            for record in records.values() if isinstance(records, dict) else []:
                if isinstance(record, dict) and record.get("id"):
                    collection.upsert(record)

    def payload(self, record: dict) -> str:
        return json.dumps(record)

    def _execute(self, query: str, params: tuple, commit: bool = False) -> Result:
        with self._lock:
            connection = self._connect()
            try:
                cursor = connection.execute(query, params)
                if commit:
                    connection.commit()
                return Result(cursor.fetchall() if query.lstrip().upper().startswith("SELECT") else [])
            finally:
                connection.close()


class PostgresStore(BaseStore):
    p = "%s"
    is_postgres = True

    def __init__(self, database_url: str):
        import psycopg
        from psycopg.types.json import Jsonb

        self._psycopg = psycopg
        self._Jsonb = Jsonb
        self.database_url = database_url
        self._lock = threading.RLock()
        self._initialize()
        self._set_collections()

    def _connect(self):
        return self._psycopg.connect(self.database_url, connect_timeout=10)

    def _initialize(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""CREATE TABLE IF NOT EXISTS records (
                    collection TEXT NOT NULL, id TEXT NOT NULL, payload JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (collection, id))""")
                cursor.execute("CREATE INDEX IF NOT EXISTS records_collection_idx ON records (collection)")

    def payload(self, record: dict):
        return self._Jsonb(record)

    def _execute(self, query: str, params: tuple, commit: bool = False) -> Result:
        with self._lock:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params)
                    rows = cursor.fetchall() if query.lstrip().upper().startswith("SELECT") else []
                if commit:
                    connection.commit()
                return Result(rows)


Store = SQLiteStore | PostgresStore


def _sqlite_path(database_url: str) -> Path:
    raw_path = database_url.removeprefix("sqlite:///")
    return Path(raw_path) if raw_path.startswith("/") else Path(raw_path).resolve()


def _create_store(database_url: str, fallback_to_sqlite: bool = True) -> Store:
    if database_url.startswith("sqlite:///"):
        return SQLiteStore(_sqlite_path(database_url))
    if database_url.startswith(("postgresql://", "postgres://")):
        try:
            return PostgresStore(database_url)
        except Exception as exc:
            if not fallback_to_sqlite:
                raise
            fallback_url = "sqlite:///./data/iabtm.db"
            print(
                "[IABTM] PostgreSQL is unavailable; using local SQLite instead. "
                "Set DATABASE_FALLBACK_TO_SQLITE=false to require PostgreSQL. "
                f"({type(exc).__name__})"
            )
            return SQLiteStore(_sqlite_path(fallback_url))
    raise ValueError("DATABASE_URL must use sqlite:/// or postgresql://")


def _normalize_supabase_database_url(database_url: str, supabase_url: str) -> str:
    """Keep the database hostname aligned with the configured Supabase project.

    This catches a common copy/paste typo in a project reference without ever
    changing credentials or a non-Supabase Postgres URL.
    """
    parsed = urlparse(database_url)
    project_host = urlparse(supabase_url).hostname or ""
    project_ref = project_host.split(".")[0]
    if not (parsed.hostname and parsed.hostname.endswith(".supabase.co") and project_ref and "@" in parsed.netloc):
        return database_url
    expected_host = f"db.{project_ref}.supabase.co"
    if parsed.hostname == expected_host:
        return database_url
    userinfo = parsed.netloc.rsplit("@", 1)[0]
    port = f":{parsed.port}" if parsed.port else ""
    return parsed._replace(netloc=f"{userinfo}@{expected_host}{port}").geturl()


settings = get_settings()
_store = _create_store(
    _normalize_supabase_database_url(settings.database_url, settings.supabase_url),
    settings.database_fallback_to_sqlite,
)


def active_database_url() -> str:
    """The URL actually in use, which is not `settings.database_url` when the
    configured PostgreSQL host was unreachable and we fell back to SQLite.

    The vector store reads this so records and embeddings can never end up
    split across two different backends.
    """
    return _store.database_url if isinstance(_store, PostgresStore) else f"sqlite:///{_store.database_path}"


def SessionLocal() -> Store:
    return _store


def get_db() -> Store:
    return _store


def init_db() -> None:
    _store._initialize()
