"""MCP server exposing llm-context-search tools for AI agents.

Start with stdio (default, works with Cursor / Claude Desktop):
    llm-context-mcp

Start with HTTP (streamable-HTTP for remote / multi-client scenarios):
    LCS_MCP_TRANSPORT=http llm-context-mcp

Configure host/port via FASTMCP_HOST / FASTMCP_PORT env vars (defaults: 127.0.0.1:8000).
"""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from llm_context_search._builder import build_engine, make_http_client
from llm_context_search.config import ContextSearchConfig

mcp = FastMCP(
    "llm-context-search",
    instructions=(
        "Retrieves up-to-date web context for LLM reasoning without calling an LLM. "
        "Prefer `build_context` - it runs the full pipeline and returns ranked text passages "
        "ready to include in your prompt. "
        "Use `search` for a quick list of URLs and snippets. "
        "Use `collect_sources` to inspect per-source fetch / extraction quality."
    ),
)

_SEARXNG_URL: str = os.getenv("SEARXNG_URL", "http://localhost:8888")
_TIMEOUT: float = float(os.getenv("LCS_TIMEOUT", "10.0"))


def _make_config(
    *,
    max_results: int = 10,
    max_sources: int = 5,
    max_passages: int = 12,
    budget_tokens: int = 4000,
) -> ContextSearchConfig:
    return ContextSearchConfig(
        max_results=max_results,
        max_sources=max_sources,
        max_passages=max_passages,
        budget_tokens=budget_tokens,
        fetch_timeout_seconds=_TIMEOUT,
    )


@mcp.tool()
async def search(
    query: str,
    language: str = "en",
    max_results: int = 10,
) -> list[dict]:
    """Search the web via SearXNG and return raw results (title, url, snippet).

    No page fetching is performed. Useful for quick URL discovery.
    """
    config = _make_config(max_results=max_results)
    async with make_http_client(_TIMEOUT) as http_client:
        engine = build_engine(_SEARXNG_URL, config, http_client)
        results = await engine.search(query, language=language, max_results=max_results)
    return [r.model_dump(exclude_none=True) for r in results]


@mcp.tool()
async def collect_sources(
    query: str,
    language: str = "en",
    max_results: int = 10,
    max_sources: int = 5,
) -> dict:
    """Search, fetch and extract source pages.

    Returns per-source fetch / extraction status and aggregated stats.
    Useful for debugging what content is available before calling build_context.
    """
    config = _make_config(max_results=max_results, max_sources=max_sources)
    async with make_http_client(_TIMEOUT) as http_client:
        engine = build_engine(_SEARXNG_URL, config, http_client)
        collection = await engine.collect_sources(
            query,
            language=language,
            max_results=max_results,
            max_sources=max_sources,
        )
    return collection.model_dump()


@mcp.tool()
async def build_context(
    query: str,
    language: str = "en",
    max_results: int = 10,
    max_sources: int = 5,
    max_passages: int = 12,
    budget_tokens: int = 4000,
) -> dict:
    """Full search-to-context pipeline: search → fetch → extract → rank → pack.

    Returns:
        context_text: Ranked, token-bounded Markdown passages ready for an LLM prompt.
        token_estimate: Approximate token count of context_text.
        stats: Pipeline statistics (results, fetched, extracted, passages, timing).
    """
    config = _make_config(
        max_results=max_results,
        max_sources=max_sources,
        max_passages=max_passages,
        budget_tokens=budget_tokens,
    )
    async with make_http_client(_TIMEOUT) as http_client:
        engine = build_engine(_SEARXNG_URL, config, http_client)
        bundle = await engine.build_context(
            query,
            language=language,
            max_results=max_results,
            max_sources=max_sources,
            max_passages=max_passages,
            budget_tokens=budget_tokens,
        )
    return {
        "context_text": bundle.context_text,
        "token_estimate": bundle.token_estimate,
        "stats": bundle.stats.model_dump(),
    }


def main() -> None:
    transport = os.getenv("LCS_MCP_TRANSPORT", "stdio")
    if transport == "http":
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
