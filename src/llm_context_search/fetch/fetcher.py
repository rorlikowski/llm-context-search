from __future__ import annotations

import asyncio

import httpx

from llm_context_search.config import FetchConfig
from llm_context_search.fetch.safety import UnsafeURLError, validate_url_is_safe


class FetchError(Exception):
    pass


class PageFetcher:
    """
    Async page fetcher with:
    - streaming (respects max_bytes limit)
    - concurrency limit via semaphore
    - timeout
    - SSRF protection (via safety.py)
    - graceful per-page error handling
    """

    def __init__(self, http_client: httpx.AsyncClient, config: FetchConfig) -> None:
        self.http_client = http_client
        self.config = config
        self._semaphore = asyncio.Semaphore(config.concurrency)

    async def fetch(self, url: str) -> str:
        try:
            validate_url_is_safe(url, block_private_ips=self.config.block_private_ips)
        except UnsafeURLError as exc:
            raise FetchError(str(exc)) from exc

        async with self._semaphore:
            try:
                async with self.http_client.stream(
                    "GET",
                    url,
                    timeout=httpx.Timeout(
                        connect=self.config.connect_timeout_seconds,
                        read=self.config.read_timeout_seconds,
                        write=5.0,
                        pool=5.0,
                    ),
                    follow_redirects=True,
                    headers={"User-Agent": self.config.user_agent},
                ) as response:
                    response.raise_for_status()

                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in response.aiter_bytes():
                        total += len(chunk)
                        if total > self.config.max_bytes:
                            break
                        chunks.append(chunk)

                raw = b"".join(chunks)
                return raw.decode("utf-8", errors="ignore")

            except httpx.HTTPStatusError as exc:
                raise FetchError(f"HTTP {exc.response.status_code}: {url}") from exc
            except httpx.TimeoutException as exc:
                raise FetchError(f"Timeout fetching: {url}") from exc
            except httpx.RequestError as exc:
                raise FetchError(f"Request error: {exc}") from exc
