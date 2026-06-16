"""Shared engine-builder utilities used by both CLI and MCP server."""

from __future__ import annotations

from typing import Any

import httpx

from llm_context_search.cache import CachedPageFetcher, CachedSearchProvider
from llm_context_search.config import ContextSearchConfig
from llm_context_search.engine import ContextSearchEngine
from llm_context_search.fetch.fetcher import PageFetcher
from llm_context_search.providers.searxng import SearXNGProvider


def make_http_client(timeout: float) -> httpx.AsyncClient:
    """Create a tuned AsyncClient with HTTP/2, keep-alive and granular timeouts."""
    return httpx.AsyncClient(
        http2=True,
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        timeout=httpx.Timeout(connect=3.0, read=timeout, write=5.0, pool=5.0),
    )


def build_engine(
    searxng_url: str,
    config: ContextSearchConfig,
    http_client: httpx.AsyncClient,
    *,
    use_cache: bool = True,
) -> ContextSearchEngine:
    """Assemble a ContextSearchEngine from config and an existing AsyncClient."""
    provider: Any = SearXNGProvider(
        base_url=searxng_url,
        http_client=http_client,
        timeout=config.searxng_timeout_seconds,
    )
    fetcher: Any = PageFetcher(http_client=http_client, config=config.to_fetch_config())

    if use_cache:
        provider = CachedSearchProvider(provider, ttl_seconds=config.search_cache_ttl_seconds)
        fetcher = CachedPageFetcher(fetcher, ttl_seconds=config.fetch_cache_ttl_seconds)

    return ContextSearchEngine(
        provider=provider,
        config=config,
        http_client=http_client,
        fetcher=fetcher,
    )
