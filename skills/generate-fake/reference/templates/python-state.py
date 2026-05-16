# Template: tiny in-memory store for stateful-lite surfaces.
# Process-local. Wiped by POST /__reset.

from collections import defaultdict
from threading import Lock

_lock = Lock()
_store: dict[str, dict[str, dict]] = defaultdict(dict)
_seq: dict[str, int] = defaultdict(int)


def put(collection: str, key: str, value: dict) -> None:
    with _lock:
        _store[collection][key] = value


def get(collection: str, key: str) -> dict | None:
    with _lock:
        return _store[collection].get(key)


def list_all(collection: str) -> list[dict]:
    with _lock:
        return list(_store[collection].values())


def next_seq(name: str) -> int:
    with _lock:
        _seq[name] += 1
        return _seq[name]


def reset() -> None:
    with _lock:
        _store.clear()
        _seq.clear()
