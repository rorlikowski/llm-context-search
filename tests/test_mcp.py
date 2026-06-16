"""Smoke tests for the MCP server – no network required."""

from __future__ import annotations

import pytest


def test_mcp_module_importable() -> None:
    import llm_context_search.mcp_server as srv

    assert hasattr(srv, "mcp")
    assert hasattr(srv, "search")
    assert hasattr(srv, "collect_sources")
    assert hasattr(srv, "build_context")
    assert hasattr(srv, "main")


@pytest.mark.asyncio
async def test_mcp_tools_registered() -> None:
    from llm_context_search.mcp_server import mcp

    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert "search" in names, f"'search' not in tools: {names}"
    assert "collect_sources" in names, f"'collect_sources' not in tools: {names}"
    assert "build_context" in names, f"'build_context' not in tools: {names}"


@pytest.mark.asyncio
async def test_build_context_tool_has_correct_params() -> None:
    from llm_context_search.mcp_server import mcp

    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "build_context")
    props = tool.inputSchema.get("properties", {})
    assert "query" in props
    assert "budget_tokens" in props
    assert "max_sources" in props
