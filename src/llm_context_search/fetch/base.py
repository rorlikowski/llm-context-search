from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PageFetcherProtocol(Protocol):
    async def fetch(self, url: str) -> str: ...
