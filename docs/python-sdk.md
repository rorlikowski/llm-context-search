# Python SDK

Embed `llm-context-search` directly in your agents, RAG pipelines or tools.

---

## Basic usage

```python
import asyncio
import httpx
from llm_context_search import ContextSearchEngine
from llm_context_search.providers import SearXNGProvider

async def main():
    async with httpx.AsyncClient() as client:
        engine = ContextSearchEngine(
            provider=SearXNGProvider(
                base_url="http://localhost:8888",
                http_client=client,
            )
        )

        bundle = await engine.build_context(
            "Python asyncio best practices",
            language="en",
            max_results=10,
            max_sources=5,
            max_passages=12,
            budget_tokens=4000,
        )

        print(bundle.context_text)
        print(f"~{bundle.token_estimate} tokens in {bundle.stats.elapsed_ms} ms")

asyncio.run(main())
```

---

## Engine methods

### `engine.build_context(query, ...)` → `ContextBundle`

Full pipeline: search → fetch → extract → rank → pack.

```python
bundle = await engine.build_context(
    "query",
    language="en",        # default: "en"
    max_results=10,       # default from config
    max_sources=5,        # default from config
    max_passages=12,      # default from config
    budget_tokens=4000,   # default from config
)

bundle.context_text      # str - Markdown passages ready for LLM
bundle.token_estimate    # int - approximate token count
bundle.sources           # list[SourceDocument]
bundle.passages          # list[Passage] - all ranked passages
bundle.selected_passages # list[Passage] - passages included in context
bundle.stats             # RetrievalStats
```

### `engine.collect_sources(query, ...)` → `SourceCollection`

Search, fetch and extract - without chunking or ranking.

```python
collection = await engine.collect_sources("query", max_sources=5)

collection.sources   # list[SourceDocument]
collection.stats     # RetrievalStats

for source in collection.sources:
    print(source.url, source.fetch_status, source.extracted_chars)
```

### `engine.search(query, ...)` → `list[SearchResult]`

Search only - no page fetching.

```python
results = await engine.search("query", language="en", max_results=10)

for r in results:
    print(r.rank, r.title, r.url, r.snippet)
```

---

## Context manager

The engine owns an internal `httpx.AsyncClient` unless you pass one. Use it as an async context manager to ensure cleanup:

```python
async with ContextSearchEngine(provider=provider) as engine:
    bundle = await engine.build_context("query")
```

---

## Configuration

Pass a `ContextSearchConfig` to tune every aspect of the pipeline:

```python
from llm_context_search import ContextSearchEngine, ContextSearchConfig
from llm_context_search.providers import SearXNGProvider

config = ContextSearchConfig(
    max_results=15,
    max_sources=8,
    max_passages=20,
    budget_tokens=8000,
    fetch_timeout_seconds=15.0,
    chunk_target_chars=1000,
    search_cache_ttl_seconds=600,
)

engine = ContextSearchEngine(provider=provider, config=config)
```

See the [Configuration reference](configuration.md) for all options.

---

## Replacing pipeline components

Every stage is a `Protocol`. Pass your own implementations to override defaults:

```python
from llm_context_search.providers.base import SearchProvider
from llm_context_search.rank.base import PassageRanker
from llm_context_search.models import SearchResult, Passage, SourceDocument

class MyProvider:
    name = "my-api"

    async def search(
        self, query: str, *, language: str = "en", max_results: int = 10
    ) -> list[SearchResult]:
        # call your own search API
        ...

class MyRanker:
    def rank(
        self, query: str, passages: list[Passage], sources: dict[str, SourceDocument]
    ) -> list[Passage]:
        # BM25, embeddings, reranker, etc.
        ...

engine = ContextSearchEngine(
    provider=MyProvider(),
    ranker=MyRanker(),
)
```

**Available protocols:**

| Protocol | Default implementation | Role |
|---|---|---|
| `SearchProvider` | `SearXNGProvider` | Fetches search results |
| `PageFetcherProtocol` | `PageFetcher` | Downloads HTML pages |
| `ContentExtractor` | `TrafilaturaExtractor` | Extracts main text |
| `PassageChunker` | `ParagraphChunker` | Splits text into passages |
| `PassageRanker` | `LexicalRanker` | Ranks passages by relevance |
| `SourceScorer` | `SourceQualityScorer` | Scores source quality |
| `ContextPacker` | `MarkdownPacker` | Packs passages to token budget |

---

## Data models

```python
from llm_context_search.models import (
    SearchResult,      # title, url, snippet, rank
    SourceDocument,    # url, fetch_status, extraction_status, extracted_text, quality_score
    Passage,           # text, source_url, lexical_score, final_score
    ContextBundle,     # context_text, token_estimate, sources, passages, stats
    SourceCollection,  # sources, stats
    RetrievalStats,    # counts + elapsed_ms
)
```
