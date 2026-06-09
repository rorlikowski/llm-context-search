from __future__ import annotations

from typing import Protocol, runtime_checkable

from llm_context_search.models import SearchResult


@runtime_checkable
class SearchProvider(Protocol):
    name: str

    async def search(
        self,
        query: str,
        *,
        language: str = "en",
        max_results: int = 10,
    ) -> list[SearchResult]: ...
