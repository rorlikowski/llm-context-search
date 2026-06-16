from __future__ import annotations

import asyncio
import time
from collections.abc import Hashable
from typing import Generic, TypeVar

_KT = TypeVar("_KT", bound=Hashable)
_VT = TypeVar("_VT")


class TTLCache(Generic[_KT, _VT]):
    """
    Thread-safe async-friendly in-memory cache with per-entry TTL.
    Uses an asyncio.Lock so all reads/writes from the same event loop are safe.
    """

    def __init__(self, ttl_seconds: float) -> None:
        self._ttl = ttl_seconds
        self._store: dict[_KT, tuple[_VT, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: _KT) -> _VT | None:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                return None
            return value

    async def set(self, key: _KT, value: _VT) -> None:
        async with self._lock:
            self._store[key] = (value, time.monotonic() + self._ttl)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()

    def __len__(self) -> int:
        return len(self._store)
