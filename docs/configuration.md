# Configuration

## `ContextSearchConfig`

Pass to `ContextSearchEngine` to control the full pipeline.

```python
from llm_context_search import ContextSearchConfig

config = ContextSearchConfig(
    max_results=10,
    budget_tokens=4000,
    fetch_timeout_seconds=10.0,
)
```

### Search & retrieval

| Field | Type | Default | Description |
|---|---|---|---|
| `max_results` | `int` | `10` | Max results fetched from SearXNG (1–50) |
| `max_sources` | `int` | `5` | Max pages to fetch and extract (1–20) |
| `max_passages` | `int` | `12` | Max passages included in context (1–100) |
| `budget_tokens` | `int` | `4000` | Token budget for context packing (500–100 000) |

### SearXNG

| Field | Type | Default | Description |
|---|---|---|---|
| `searxng_timeout_seconds` | `float` | `5.0` | Timeout for SearXNG API calls |

### Fetching

| Field | Type | Default | Description |
|---|---|---|---|
| `fetch_timeout_seconds` | `float` | `6.0` | Read timeout per page request |
| `fetch_connect_timeout_seconds` | `float` | `3.0` | TCP connect timeout |
| `max_fetch_bytes` | `int` | `1 000 000` | Max bytes downloaded per page (1 MB) |
| `max_redirects` | `int` | `3` | Max HTTP redirects followed (0–10) |
| `fetch_concurrency` | `int` | `5` | Parallel page fetches (1–20) |
| `user_agent` | `str` | `llm-context-search/0.1` | User-Agent header |

### Security

| Field | Type | Default | Description |
|---|---|---|---|
| `block_private_ips` | `bool` | `True` | Block fetching private / loopback IPs (SSRF protection) |
| `allow_http` | `bool` | `True` | Allow `http://` URLs |
| `allow_https` | `bool` | `True` | Allow `https://` URLs |

### Chunking

| Field | Type | Default | Description |
|---|---|---|---|
| `chunk_target_chars` | `int` | `1200` | Target chunk size in characters (300–5000) |
| `chunk_max_chars` | `int` | `2000` | Hard max chunk size (500–8000) |
| `chunk_overlap_chars` | `int` | `150` | Overlap between adjacent chunks (0–1000) |

### Caching

In-memory TTL cache - speeds up repeated queries within the same process.

| Field | Type | Default | Description |
|---|---|---|---|
| `search_cache_ttl_seconds` | `float` | `300.0` | TTL for cached SearXNG responses |
| `fetch_cache_ttl_seconds` | `float` | `300.0` | TTL for cached page HTML |

Set to `0` to disable caching.

---

## CLI flags

All CLI commands accept these flags (mapped to `ContextSearchConfig` fields):

| Flag | Config field | Default |
|---|---|---|
| `--searxng-url` / `-u` | - | `http://localhost:8888` |
| `--language` / `-l` | - | `en` |
| `--max-results` | `max_results` | `10` |
| `--max-sources` | `max_sources` | `5` |
| `--max-passages` | `max_passages` | `12` |
| `--budget` | `budget_tokens` | `4000` |
| `--timeout` | `fetch_timeout_seconds` | `10.0` |
| `--no-cache` | - | off |

---

## MCP server environment variables

| Variable | Default | Description |
|---|---|---|
| `SEARXNG_URL` | `http://localhost:8888` | SearXNG instance URL |
| `LCS_TIMEOUT` | `10.0` | HTTP timeout for all requests |
| `LCS_MCP_TRANSPORT` | `stdio` | MCP transport: `stdio` or `http` |
| `FASTMCP_HOST` | `127.0.0.1` | HTTP transport bind address |
| `FASTMCP_PORT` | `8000` | HTTP transport port |
