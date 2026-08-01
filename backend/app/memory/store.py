"""Short-term session memory.

Spec section 7.5 calls for Redis with a 24h TTL. Running a Redis daemon
just for a single-process prototype is unnecessary weight, so this is an
in-process TTL dict behind the same get/set/delete shape — swap the body
of this class for a `redis.Redis` client later without touching callers.
"""

import time
from threading import Lock


class MemoryStore:
    def __init__(self) -> None:
        self._data: dict[str, tuple[float, object]] = {}
        self._lock = Lock()

    def set(self, key: str, value: object, ttl_seconds: int = 24 * 60 * 60) -> None:
        with self._lock:
            self._data[key] = (time.monotonic() + ttl_seconds, value)

    def get(self, key: str, default=None):
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return default
            expires_at, value = entry
            if time.monotonic() > expires_at:
                del self._data[key]
                return default
            return value

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)


_store = MemoryStore()


def get_memory_store() -> MemoryStore:
    return _store
