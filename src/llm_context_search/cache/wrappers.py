from __future__ import annotations

from llm_context_search.cache.ttl import TTLCache
from llm_context_search.models import SearchResult


class CachedSearchProvider:
    """
    Wraps any SearchProvider and caches results in memory for `ttl_seconds`.
    Cache key: (query, language, max_results).
    """

    def __init__(self, provider: object, ttl_seconds: float = 300.0) -> None:
        self._provider = provider
        self._cache: TTLCache[tuple[str, str, int], list[SearchResult]] = TTLCache(ttl_seconds)

    @property
    def name(self) -> str:
        return getattr(self._provider, "name", "cached")

    async def search(
        self,
        query: str,
        *,
        language: str = "en",
        max_results: int = 10,
    ) -> list[SearchResult]:
        key = (query, language, max_results)
        cached = await self._cache.get(key)
        if cached is not None:
            return cached
        results = await self._provider.search(query, language=language, max_results=max_results)  # type: ignore[attr-defined]
        await self._cache.set(key, results)
        return results


class CachedPageFetcher:
    """
    Wraps any PageFetcherProtocol and caches raw HTML per URL for `ttl_seconds`.
    """

    def __init__(self, fetcher: object, ttl_seconds: float = 300.0) -> None:
        self._fetcher = fetcher
        self._cache: TTLCache[str, str] = TTLCache(ttl_seconds)

    async def fetch(self, url: str) -> str:
        cached = await self._cache.get(url)
        if cached is not None:
            return cached
        html = await self._fetcher.fetch(url)  # type: ignore[attr-defined]
        await self._cache.set(url, html)
        return html
