# llm-context-search

> Fast LLM-free search-to-context engine for AI agents.

`llm-context-search` turns web search results into clean, ranked and token-bounded context for LLM applications.

It searches via SearXNG, fetches pages, extracts main content, ranks relevant passages and packs them into a compact `ContextBundle` — **without using an LLM**.

Self-hosted friendly. Built for agents, RAG and local LLM workflows.

---

## Pipeline

```
query
  ↓
SearXNGProvider
  ↓
URL normalization + deduplication
  ↓
safe async fetch (httpx)
  ↓
content extraction (Trafilatura + BS4 fallback)
  ↓
source quality scoring
  ↓
paragraph chunking
  ↓
lexical passage ranking
  ↓
context packing (token budget)
  ↓
ContextBundle → console / file
```

---

## Quickstart

### 1. Start SearXNG

```bash
# Create config dir and start
mkdir -p searxng
docker compose up -d
```

Then edit `searxng/settings.yml` and make sure JSON format is enabled:

```yaml
search:
  formats:
    - html
    - json
```

Restart if needed: `docker compose restart searxng`

### 2. Install

Requires Python 3.11+.

```bash
# With uv (recommended)
uv venv
uv pip install -e .

# Or with pip
pip install -e .
```

### 3. Use the CLI

```bash
# Search only (no page fetching)
llm-context search "Pydantic AI tools" --searxng-url http://localhost:8888

# Fetch and extract sources, show status
llm-context collect "Pydantic AI tools" --max-sources 5

# Full pipeline: build context ready for an LLM
llm-context build "Pydantic AI tools" --budget 4000 --max-sources 5

# Save result to file
llm-context build "Pydantic AI tools" --budget 4000 -o context.md

# JSON output (pipe to jq, save, feed to LLM)
llm-context build "Pydantic AI tools" --json
llm-context build "Pydantic AI tools" --json -o bundle.json

# Verbose mode (shows per-source fetch/extract stats)
llm-context build "Pydantic AI tools" --verbose
```

All commands accept these options:

| Option | Default | Description |
|---|---|---|
| `--searxng-url` / `-u` | `http://localhost:8888` | SearXNG base URL (also `SEARXNG_URL` env var) |
| `--language` / `-l` | `en` | Search language |
| `--max-results` | `10` | Max results from provider |
| `--max-sources` | `5` | Max pages to fetch |
| `--max-passages` | `12` | Max passages in context |
| `--budget` | `4000` | Token budget |
| `--timeout` | `10.0` | HTTP timeout (seconds) |
| `--json` | off | Output raw JSON |
| `--output` / `-o` | — | Write output to file |
| `--verbose` / `-v` | off | Show source details |

---

## Python SDK

```python
import asyncio
import httpx
from llm_context_search import ContextSearchEngine
from llm_context_search.providers import SearXNGProvider

async def main():
    async with httpx.AsyncClient() as http_client:
        engine = ContextSearchEngine(
            provider=SearXNGProvider(
                base_url="http://localhost:8888",
                http_client=http_client,
            )
        )

        bundle = await engine.build_context(
            "Pydantic AI tools and toolsets",
            language="en",
            max_results=10,
            max_sources=5,
            max_passages=12,
            budget_tokens=4000,
        )

        print(bundle.context_text)
        print(f"~{bundle.token_estimate} tokens, {bundle.stats.elapsed_ms} ms")

asyncio.run(main())
```

### Replacing components (SOLID / open-closed)

Every pipeline stage is behind a `Protocol`. Pass your own implementation to `ContextSearchEngine`:

```python
from llm_context_search.providers.base import SearchProvider
from llm_context_search.rank.base import PassageRanker

class MyProvider:
    name = "my-provider"
    async def search(self, query, *, language="en", max_results=10):
        ...  # call your own search API

class MyRanker:
    def rank(self, query, passages, sources):
        ...  # custom ranking (BM25, embeddings, etc.)

engine = ContextSearchEngine(
    provider=MyProvider(),
    ranker=MyRanker(),
)
```

Protocols: `SearchProvider`, `PageFetcherProtocol`, `ContentExtractor`, `PassageChunker`, `PassageRanker`, `SourceScorer`, `ContextPacker`.

---

## Architecture

```
src/llm_context_search/
├── engine.py              # ContextSearchEngine (orchestrator)
├── models.py              # Pydantic data models
├── config.py              # ContextSearchConfig, FetchConfig
├── cli.py                 # Typer CLI (search / collect / build)
├── providers/
│   ├── base.py            # SearchProvider Protocol
│   └── searxng.py         # SearXNGProvider
├── fetch/
│   ├── base.py            # PageFetcherProtocol
│   ├── fetcher.py         # PageFetcher (async, streaming)
│   └── safety.py          # SSRF / private IP / scheme validation
├── extract/
│   ├── base.py            # ContentExtractor Protocol
│   ├── trafilatura.py     # TrafilaturaExtractor (primary)
│   └── fallback.py        # FallbackExtractor (BS4)
├── normalize/urls.py      # normalize_url
├── dedupe/urls.py         # deduplicate_results
├── chunk/
│   ├── base.py            # PassageChunker Protocol
│   └── paragraph.py       # ParagraphChunker
├── rank/
│   ├── base.py            # PassageRanker, SourceScorer Protocols
│   ├── quality.py         # SourceQualityScorer
│   └── lexical.py         # LexicalRanker
├── pack/
│   ├── base.py            # ContextPacker Protocol
│   └── markdown.py        # MarkdownPacker
└── utils/
    ├── hashing.py
    ├── tokens.py
    ├── timing.py
    └── text.py
```

---

## Security

- Only `http` and `https` schemes are allowed.
- Private IPs and `localhost` are blocked by default (`block_private_ips=True`) to prevent SSRF.
- Each page fetch has a timeout (default 10s) and a max bytes limit (default 1 MB).
- Redirects are validated against the same safety rules.

**Responsible use:**
- Do not use as an aggressive crawler.
- Respect search provider terms of service.
- Do not expose a public SearXNG instance without rate limiting.

---

## Roadmap

- **v0.2** — BM25 ranking, MMR diversity, SQLite cache, `tiktoken` support
- **v0.3** — MCP server, Pydantic AI toolset, LangChain tool, FastAPI server mode
- **v0.4** — Dify plugin, n8n node
- **v0.5** — Multi-provider (Brave, DuckDuckGo, Tavily)
- **v1.0** — Stable API, benchmarks, production security defaults

---

## Development

```bash
uv venv
uv pip install -e ".[dev]"
ruff check src/
ruff format src/
pytest
```
