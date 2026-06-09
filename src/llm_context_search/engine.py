from __future__ import annotations

import asyncio
import functools

import httpx

from llm_context_search.chunk.base import PassageChunker
from llm_context_search.chunk.paragraph import ParagraphChunker
from llm_context_search.config import ContextSearchConfig
from llm_context_search.dedupe.urls import deduplicate_results
from llm_context_search.extract.base import ContentExtractor
from llm_context_search.extract.fallback import FallbackExtractor
from llm_context_search.extract.trafilatura import TrafilaturaExtractor
from llm_context_search.fetch.base import PageFetcherProtocol
from llm_context_search.fetch.fetcher import FetchError, PageFetcher
from llm_context_search.models import (
    ContextBundle,
    Passage,
    RetrievalStats,
    SearchResult,
    SourceCollection,
    SourceDocument,
)
from llm_context_search.normalize.urls import normalize_url
from llm_context_search.pack.base import ContextPacker
from llm_context_search.pack.markdown import MarkdownPacker
from llm_context_search.providers.base import SearchProvider
from llm_context_search.rank.base import PassageRanker, SourceScorer
from llm_context_search.rank.lexical import LexicalRanker
from llm_context_search.rank.quality import SourceQualityScorer
from llm_context_search.utils.hashing import sha256_hash
from llm_context_search.utils.timing import Timer
from llm_context_search.utils.tokens import estimate_tokens


class ContextSearchEngine:
    """
    Orchestrates the full search-to-context pipeline:
      search → normalize → dedupe → fetch → extract → score → chunk → rank → pack

    All components are injected via constructor (DI / SOLID open-closed principle).
    Missing components default to the built-in implementations.
    """

    def __init__(
        self,
        provider: SearchProvider,
        extractor: ContentExtractor | None = None,
        fetcher: PageFetcherProtocol | None = None,
        chunker: PassageChunker | None = None,
        ranker: PassageRanker | None = None,
        packer: ContextPacker | None = None,
        scorer: SourceScorer | None = None,
        config: ContextSearchConfig | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config or ContextSearchConfig()
        self.provider = provider

        self._own_http_client = http_client is None
        self._http_client = http_client or httpx.AsyncClient()

        self.extractor: ContentExtractor = extractor or TrafilaturaExtractor()
        self._fallback_extractor = FallbackExtractor()

        self.fetcher: PageFetcherProtocol = fetcher or PageFetcher(
            http_client=self._http_client,
            config=self.config.to_fetch_config(),
        )
        self.chunker: PassageChunker = chunker or ParagraphChunker(
            target_chars=self.config.chunk_target_chars,
            max_chars=self.config.chunk_max_chars,
            overlap_chars=self.config.chunk_overlap_chars,
        )
        self.ranker: PassageRanker = ranker or LexicalRanker()
        self.packer: ContextPacker = packer or MarkdownPacker()
        self.scorer: SourceScorer = scorer or SourceQualityScorer()

    async def __aenter__(self) -> ContextSearchEngine:
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._own_http_client:
            await self._http_client.aclose()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        *,
        language: str = "en",
        max_results: int | None = None,
    ) -> list[SearchResult]:
        """Search only – returns raw SearchResult list without fetching pages."""
        n = max_results or self.config.max_results
        results = await self.provider.search(query, language=language, max_results=n)
        for r in results:
            r.normalized_url = normalize_url(r.url)
        return results

    async def collect_sources(
        self,
        query: str,
        *,
        language: str = "en",
        max_results: int | None = None,
        max_sources: int | None = None,
    ) -> SourceCollection:
        """Search, deduplicate, fetch and extract – returns SourceCollection."""
        timer = Timer()
        n_results = max_results or self.config.max_results
        n_sources = max_sources or self.config.max_sources

        raw_results = await self.provider.search(query, language=language, max_results=n_results)
        unique = deduplicate_results(raw_results)
        selected = unique[:n_sources]

        sources = await self._fetch_and_extract(selected, query)

        stats = RetrievalStats(
            search_results_count=len(raw_results),
            unique_urls_count=len(unique),
            skipped_duplicate_urls_count=len(raw_results) - len(unique),
            fetched_count=sum(1 for s in sources if s.fetch_status == "ok"),
            failed_fetch_count=sum(1 for s in sources if s.fetch_status == "failed"),
            extracted_count=sum(1 for s in sources if s.extraction_status == "ok"),
            failed_extraction_count=sum(1 for s in sources if s.extraction_status == "failed"),
            empty_extraction_count=sum(1 for s in sources if s.extraction_status == "empty"),
            elapsed_ms=timer.elapsed_ms(),
        )
        return SourceCollection(query=query, sources=sources, stats=stats)

    async def build_context(
        self,
        query: str,
        *,
        language: str = "en",
        max_results: int | None = None,
        max_sources: int | None = None,
        max_passages: int | None = None,
        budget_tokens: int | None = None,
    ) -> ContextBundle:
        """Full pipeline – returns ContextBundle with context_text ready for LLM."""
        timer = Timer()
        n_results = max_results or self.config.max_results
        n_sources = max_sources or self.config.max_sources
        n_passages = max_passages or self.config.max_passages
        budget = budget_tokens or self.config.budget_tokens

        raw_results = await self.provider.search(query, language=language, max_results=n_results)
        unique = deduplicate_results(raw_results)
        selected = unique[:n_sources]

        sources = await self._fetch_and_extract(selected, query)
        sources_by_url = {s.url: s for s in sources}

        all_passages: list[Passage] = []
        for source in sources:
            if source.extracted_text:
                all_passages.extend(self.chunker.chunk(source))

        ranked_passages = self.ranker.rank(query, all_passages, sources_by_url)
        context_text, selected_passages = self.packer.pack(ranked_passages, budget, n_passages)
        token_est = estimate_tokens(context_text)

        stats = RetrievalStats(
            search_results_count=len(raw_results),
            unique_urls_count=len(unique),
            skipped_duplicate_urls_count=len(raw_results) - len(unique),
            fetched_count=sum(1 for s in sources if s.fetch_status == "ok"),
            failed_fetch_count=sum(1 for s in sources if s.fetch_status == "failed"),
            extracted_count=sum(1 for s in sources if s.extraction_status == "ok"),
            failed_extraction_count=sum(1 for s in sources if s.extraction_status == "failed"),
            empty_extraction_count=sum(1 for s in sources if s.extraction_status == "empty"),
            passages_count=len(all_passages),
            selected_passages_count=len(selected_passages),
            token_estimate=token_est,
            elapsed_ms=timer.elapsed_ms(),
        )

        return ContextBundle(
            query=query,
            sources=sources,
            passages=ranked_passages,
            selected_passages=selected_passages,
            context_text=context_text,
            token_estimate=token_est,
            stats=stats,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _fetch_and_extract(self, results: list[SearchResult], query: str) -> list[SourceDocument]:
        tasks = [self._process_one(r, query) for r in results]
        return list(await asyncio.gather(*tasks))

    async def _process_one(self, result: SearchResult, query: str) -> SourceDocument:
        normalized_url = result.normalized_url or normalize_url(result.url)

        # Fetch
        html: str | None = None
        fetch_status: str = "failed"
        error: str | None = None
        try:
            html = await self.fetcher.fetch(result.url)
            fetch_status = "ok"
        except FetchError as exc:
            error = str(exc)
        except Exception as exc:
            error = f"Unexpected fetch error: {exc}"

        # Extract (run in thread pool to avoid blocking the event loop)
        extracted_text: str | None = None
        extraction_status: str = "skipped"
        title = result.title

        if html is not None:
            content = await asyncio.to_thread(functools.partial(self.extractor.extract, html, url=result.url))
            extracted_text = content.text

            if not extracted_text:
                fallback_content = await asyncio.to_thread(
                    functools.partial(self._fallback_extractor.extract, html, url=result.url)
                )
                extracted_text = fallback_content.text

            if extracted_text:
                extraction_status = "ok"
                if content.title:
                    title = content.title
            else:
                extraction_status = "empty"

        extracted_chars = len(extracted_text) if extracted_text else 0

        doc = SourceDocument(
            title=title,
            url=result.url,
            normalized_url=normalized_url,
            snippet=result.snippet,
            provider=result.provider,
            fetch_status=fetch_status,  # type: ignore[arg-type]
            extraction_status=extraction_status,  # type: ignore[arg-type]
            extracted_text=extracted_text,
            extracted_chars=extracted_chars,
            token_estimate=estimate_tokens(extracted_text) if extracted_text else 0,
            content_hash=sha256_hash(extracted_text) if extracted_text else None,
            quality_score=0.0,
            error=error,
        )
        doc.quality_score = self.scorer.score(doc, query)
        return doc
