"""Local JSON-file storage layer.

Spec section 10 calls for PostgreSQL (+ pgvector for embeddings). Running a
Postgres server for a single-process prototype is unnecessary weight, so
plain records (users, goals, interactions, agent runs...) live in flat JSON
files on disk instead — one file per collection, atomic writes, no server
process. Each collection exposes get/all/filter/upsert/delete, the same
shape a real repository would — that's the seam to swap for a Postgres/Mongo
client later without touching any caller.

Embeddings are deliberately NOT stored here — they go through
`app.embeddings.vector_store`, which is the piece actually worth swapping
for a real vector DB (Qdrant/Chroma/pgvector) later. See that module.
"""

import json
import os
import threading
from collections.abc import Callable
from pathlib import Path

from app.config import get_settings


class Record(dict):
    """Dict that also allows attribute access (`record.field`, including
    assignment), so code written against ORM-style objects keeps working
    unchanged against plain JSON-backed dicts."""

    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value) -> None:
        self[name] = value


class JSONCollection:
    """One JSON file on disk = one collection of Records keyed by `id`."""

    def __init__(self, path: Path):
        self._path = path
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write({})

    def _read(self) -> dict:
        if not self._path.exists():
            return {}
        raw = self._path.read_text().strip()
        return json.loads(raw) if raw else {}

    def _write(self, data: dict) -> None:
        # Write-then-rename keeps a crash mid-write from corrupting the file.
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        os.replace(tmp, self._path)

    def get(self, id: str) -> Record | None:
        with self._lock:
            doc = self._read().get(id)
            return Record(doc) if doc is not None else None

    def all(self) -> list[Record]:
        with self._lock:
            return [Record(d) for d in self._read().values()]

    def filter(self, predicate: Callable[[dict], bool]) -> list[Record]:
        with self._lock:
            return [Record(d) for d in self._read().values() if predicate(d)]

    def count(self) -> int:
        with self._lock:
            return len(self._read())

    def upsert(self, record: dict) -> Record:
        with self._lock:
            data = self._read()
            data[record["id"]] = dict(record)
            self._write(data)
            return Record(record)

    def delete(self, id: str) -> None:
        with self._lock:
            data = self._read()
            data.pop(id, None)
            self._write(data)


class Store:
    """All local collections in one place. One process-wide instance."""

    def __init__(self, base_dir: Path):
        self.users = JSONCollection(base_dir / "users.json")
        self.identity_nodes = JSONCollection(base_dir / "identity_nodes.json")
        self.goals = JSONCollection(base_dir / "goals.json")
        self.content_items = JSONCollection(base_dir / "content_items.json")
        self.interaction_events = JSONCollection(base_dir / "interaction_events.json")
        self.agent_runs = JSONCollection(base_dir / "agent_runs.json")
        self.agent_step_logs = JSONCollection(base_dir / "agent_step_logs.json")

    # Context-manager compatibility so existing `with SessionLocal() as db:`
    # call sites don't need to change — there's no connection to open/close.
    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc_info) -> None:
        return None


settings = get_settings()
_store = Store(Path(settings.data_dir))


def SessionLocal() -> Store:
    return _store


def get_db() -> Store:
    return _store


def init_db() -> None:
    pass  # JSON collections create their files lazily on first access.
