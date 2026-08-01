"""SQLite-backed persistence with the existing repository-shaped API.

Each record is stored as JSON in SQLite, which gives the prototype durable,
atomic, queryable storage without forcing every caller to change at once.
The collection API intentionally matches the old JSON store, so the rest of
the application remains ready for a future typed Postgres migration.
"""

import json
import sqlite3
import threading
from collections.abc import Callable
from pathlib import Path

from app.config import get_settings


class Record(dict):
    """Dict with attribute access, compatible with the former model shapes."""

    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value) -> None:
        self[name] = value


class SQLiteCollection:
    def __init__(self, store: "Store", name: str):
        self._store = store
        self._name = name

    def get(self, id: str) -> Record | None:
        row = self._store._execute(
            "SELECT payload FROM records WHERE collection = ? AND id = ?", (self._name, id)
        ).fetchone()
        return Record(json.loads(row[0])) if row else None

    def all(self) -> list[Record]:
        rows = self._store._execute(
            "SELECT payload FROM records WHERE collection = ? ORDER BY rowid", (self._name,)
        ).fetchall()
        return [Record(json.loads(row[0])) for row in rows]

    def filter(self, predicate: Callable[[dict], bool]) -> list[Record]:
        return [record for record in self.all() if predicate(record)]

    def count(self) -> int:
        row = self._store._execute(
            "SELECT COUNT(*) FROM records WHERE collection = ?", (self._name,)
        ).fetchone()
        return int(row[0])

    def upsert(self, record: dict) -> Record:
        saved = dict(record)
        if not saved.get("id"):
            raise ValueError("Records must have an id")
        self._store._execute(
            """INSERT INTO records (collection, id, payload) VALUES (?, ?, ?)
               ON CONFLICT(collection, id) DO UPDATE SET payload = excluded.payload""",
            (self._name, saved["id"], json.dumps(saved)),
            commit=True,
        )
        return Record(saved)

    def delete(self, id: str) -> None:
        self._store._execute(
            "DELETE FROM records WHERE collection = ? AND id = ?", (self._name, id), commit=True
        )


class Store:
    """Process-wide SQLite store. Connections are short-lived and thread-safe."""

    collection_names = (
        "users", "identity_nodes", "goals", "content_items", "interaction_events",
        "agent_runs", "agent_step_logs",
    )

    def __init__(self, database_path: Path):
        self.database_path = database_path
        self._lock = threading.RLock()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()
        for name in self.collection_names:
            setattr(self, name, SQLiteCollection(self, name))
        self._migrate_legacy_json(database_path.parent)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS records (
                    collection TEXT NOT NULL,
                    id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    PRIMARY KEY (collection, id)
                )"""
            )
            connection.execute("CREATE INDEX IF NOT EXISTS records_collection_idx ON records (collection)")

    def _migrate_legacy_json(self, legacy_dir: Path) -> None:
        """One-time import of the prototype's existing JSON data, if present."""
        for name in self.collection_names:
            source = legacy_dir / f"{name}.json"
            collection = getattr(self, name)
            if collection.count() or not source.exists():
                continue
            try:
                records = json.loads(source.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(records, dict):
                for record in records.values():
                    if isinstance(record, dict) and record.get("id"):
                        collection.upsert(record)

    def _execute(self, query: str, params: tuple, commit: bool = False):
        with self._lock:
            connection = self._connect()
            try:
                cursor = connection.execute(query, params)
                if commit:
                    connection.commit()
                # Materialize reads before the connection is closed.
                if query.lstrip().upper().startswith("SELECT"):
                    rows = cursor.fetchall()
                    class Result:
                        def fetchone(self_inner):
                            return rows[0] if rows else None
                        def fetchall(self_inner):
                            return rows
                    return Result()
                return cursor
            finally:
                connection.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc_info) -> None:
        return None


def _sqlite_path(database_url: str) -> Path:
    if not database_url.startswith("sqlite:///"):
        raise ValueError("Only SQLite DATABASE_URL values are supported in this build.")
    raw_path = database_url.removeprefix("sqlite:///")
    return Path(raw_path) if raw_path.startswith("/") else Path(raw_path).resolve()


settings = get_settings()
_store = Store(_sqlite_path(settings.database_url))


def SessionLocal() -> Store:
    return _store


def get_db() -> Store:
    return _store


def init_db() -> None:
    """Initialize schema; called on API startup and safe to run repeatedly."""
    _store._initialize()
