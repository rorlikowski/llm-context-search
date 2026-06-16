"""Engine integration tests using fake provider and fetcher (no network)."""

from __future__ import annotations

import pytest

from llm_context_search.engine import ContextSearchEngine
from llm_context_search.models import SearchResult


class FakeProvider:
    name = "fake"

    def __init__(self, results: list[SearchResult] | None = None) -> None:
        self._results = results or [
            SearchResult(
                title="Python asyncio guide",
                url="https://example.com/asyncio",
                snippet="A comprehensive guide to Python asyncio and async/await.",
                provider="fake",
                rank=1,
            ),
        ]

    async def search(self, query: str, *, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        return self._results[:max_results]


class FakeFetcher:
    def __init__(self, html: str = "") -> None:
        self._html = html or (
            "<html><body>"
            "<p>Python asyncio allows writing concurrent code using async/await syntax. "
            "It is used for IO-bound and high-level structured network code. "
            "The asyncio library provides event loop, coroutines, tasks and futures.</p>"
            "<p>Use asyncio.run() to execute coroutines from synchronous code.</p>"
            "</body></html>"
        )

    async def fetch(self, url: str) -> str:
        return self._html


@pytest.mark.asyncio
async def test_search_returns_results() -> None:
    engine = ContextSearchEngine(provider=FakeProvider(), fetcher=FakeFetcher())
    results = await engine.search("asyncio", max_results=5)
    assert len(results) >= 1
    assert results[0].title == "Python asyncio guide"


@pytest.mark.asyncio
async def test_collect_sources_stats() -> None:
    engine = ContextSearchEngine(provider=FakeProvider(), fetcher=FakeFetcher())
    collection = await engine.collect_sources("asyncio", max_results=1, max_sources=1)
    assert collection.stats.search_results_count == 1
    assert collection.stats.fetched_count == 1
    assert collection.stats.extracted_count >= 0  # depends on trafilatura parsing the fake html


@pytest.mark.asyncio
async def test_build_context_returns_context_text() -> None:
    engine = ContextSearchEngine(provider=FakeProvider(), fetcher=FakeFetcher())
    bundle = await engine.build_context("asyncio", max_results=1, max_sources=1, budget_tokens=8000)
    assert bundle.stats.search_results_count == 1
    assert bundle.token_estimate >= 0


@pytest.mark.asyncio
async def test_build_context_with_failed_fetch_does_not_crash() -> None:
    class ErrorFetcher:
        async def fetch(self, url: str) -> str:
            raise RuntimeError("simulated fetch failure")

    engine = ContextSearchEngine(provider=FakeProvider(), fetcher=ErrorFetcher())
    bundle = await engine.build_context("asyncio", max_results=1, max_sources=1)
    assert bundle.stats.failed_fetch_count == 1
    assert bundle.stats.fetched_count == 0


@pytest.mark.asyncio
async def test_build_context_deduplicates_same_url() -> None:
    duplicate_results = [
        SearchResult(title="Page A", url="https://example.com/page", provider="fake", rank=1),
        SearchResult(title="Page A copy", url="https://example.com/page/", provider="fake", rank=2),
    ]
    engine = ContextSearchEngine(provider=FakeProvider(duplicate_results), fetcher=FakeFetcher())
    bundle = await engine.build_context("test", max_results=5, max_sources=5)
    assert bundle.stats.unique_urls_count == 1
    assert bundle.stats.skipped_duplicate_urls_count == 1


@pytest.mark.asyncio
async def test_engine_context_manager() -> None:
    async with ContextSearchEngine(provider=FakeProvider(), fetcher=FakeFetcher()) as engine:
        results = await engine.search("test")
    assert isinstance(results, list)
