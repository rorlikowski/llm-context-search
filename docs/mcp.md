# MCP Server

`llm-context-search` ships a built-in [Model Context Protocol](https://modelcontextprotocol.io/) server that exposes the search-to-context pipeline as three tools any MCP-compatible agent can call.

---

## Quick setup

### Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "llm-context-search": {
      "command": "llm-context-mcp",
      "env": {
        "SEARXNG_URL": "http://localhost:8888"
      }
    }
  }
}
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "llm-context-search": {
      "command": "llm-context-mcp",
      "env": {
        "SEARXNG_URL": "http://localhost:8888"
      }
    }
  }
}
```

### Using `uvx` (no global install needed)

If you don't want to install the package globally, use `uvx`:

```json
{
  "mcpServers": {
    "llm-context-search": {
      "command": "uvx",
      "args": ["llm-context-mcp"],
      "env": {
        "SEARXNG_URL": "http://localhost:8888"
      }
    }
  }
}
```

---

## Transports

### stdio (default)

Used by Cursor, Claude Desktop and most local MCP clients. Starts automatically when the client launches `llm-context-mcp`.

### Streamable HTTP

For remote deployments or multi-client scenarios:

```bash
LCS_MCP_TRANSPORT=http llm-context-mcp
```

The endpoint is available at `http://<host>:<port>/mcp`.

Configure with environment variables:

| Variable | Default | Description |
|---|---|---|
| `FASTMCP_HOST` | `127.0.0.1` | Bind address |
| `FASTMCP_PORT` | `8000` | Port |

---

## Available tools

### `build_context` ⭐ recommended

Runs the full search → fetch → extract → rank → pack pipeline.

Returns:

- `context_text` - Markdown-formatted passages, ready to include in an LLM prompt
- `token_estimate` - approximate token count
- `stats` - pipeline statistics (results, fetched, extracted, passages, timing)

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | *(required)* | Search query |
| `language` | `str` | `"en"` | Search language code |
| `max_results` | `int` | `10` | Max results from SearXNG |
| `max_sources` | `int` | `5` | Max pages to fetch |
| `max_passages` | `int` | `12` | Max passages in output |
| `budget_tokens` | `int` | `4000` | Token budget |

**Example agent prompt:**

> Search for "Python asyncio pitfalls" and build me context with a 6000 token budget.

---

### `search`

Searches via SearXNG and returns raw results - titles, URLs and snippets. No page fetching.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | *(required)* | Search query |
| `language` | `str` | `"en"` | Search language code |
| `max_results` | `int` | `10` | Number of results |

Useful when the agent only needs to know *which* pages exist, not their content.

---

### `collect_sources`

Fetches and extracts source pages. Returns per-source fetch/extraction status and aggregated stats.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | *(required)* | Search query |
| `language` | `str` | `"en"` | Search language code |
| `max_results` | `int` | `10` | Max results from SearXNG |
| `max_sources` | `int` | `5` | Max pages to fetch |

Useful for debugging - lets the agent see which sources were extracted successfully before calling `build_context`.

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `SEARXNG_URL` | `http://localhost:8888` | SearXNG instance URL |
| `LCS_TIMEOUT` | `10.0` | HTTP timeout in seconds |
| `LCS_MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `http` |
| `FASTMCP_HOST` | `127.0.0.1` | HTTP server host (http transport only) |
| `FASTMCP_PORT` | `8000` | HTTP server port (http transport only) |

---

## How agents should use these tools

```
Agent decides to look something up
  → calls build_context(query="...", budget_tokens=4000)
  → receives context_text with ranked passages
  → includes context_text in next LLM call

If unsure whether content is available:
  → calls collect_sources first to check fetch/extraction status
  → then calls build_context if sources are good

For quick URL discovery only:
  → calls search(query="...")
```
