from __future__ import annotations

import httpx

from llm_context_search.models import SearchResult


class SearXNGProvider:
    name = "searxng"

    def __init__(self, base_url: str, http_client: httpx.AsyncClient, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.http_client = http_client
        self.timeout = timeout

    async def search(
        self,
        query: str,
        *,
        language: str = "en",
        max_results: int = 10,
    ) -> list[SearchResult]:
        response = await self.http_client.get(
            f"{self.base_url}/search",
            params={
                "q": query,
                "format": "json",
                "language": language,
                "safesearch": 1,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()

        results: list[SearchResult] = []
        for index, item in enumerate(data.get("results", [])[:max_results], start=1):
            title = item.get("title") or ""
            url = item.get("url") or ""
            if not title or not url:
                continue
            results.append(
                SearchResult(
                    title=title,
                    url=url,
                    snippet=item.get("content"),
                    provider=self.name,
                    rank=index,
                    raw_score=item.get("score"),
                )
            )

        return results
