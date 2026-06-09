from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Annotated

import httpx
import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from llm_context_search.cache import CachedPageFetcher, CachedSearchProvider
from llm_context_search.config import ContextSearchConfig
from llm_context_search.engine import ContextSearchEngine
from llm_context_search.providers.searxng import SearXNGProvider

app = typer.Typer(
    name="llm-context",
    help="Fast LLM-free search-to-context engine for AI agents.",
    add_completion=False,
)

console = Console()
err_console = Console(stderr=True)

# ---------------------------------------------------------------------------
# Common options
# ---------------------------------------------------------------------------

SearxngUrl = Annotated[str, typer.Option("--searxng-url", "-u", envvar="SEARXNG_URL", help="SearXNG base URL")]
Language = Annotated[str, typer.Option("--language", "-l", help="Search language code")]
MaxResults = Annotated[int, typer.Option("--max-results", help="Max search results to fetch from provider")]
MaxSources = Annotated[int, typer.Option("--max-sources", help="Max pages to fetch and extract")]
MaxPassages = Annotated[int, typer.Option("--max-passages", help="Max passages to include in context")]
Budget = Annotated[int, typer.Option("--budget", help="Token budget for context packing")]
Timeout = Annotated[float, typer.Option("--timeout", help="HTTP request timeout in seconds")]
NoCache = Annotated[bool, typer.Option("--no-cache", is_flag=True, help="Disable in-memory TTL cache")]
AsJson = Annotated[bool, typer.Option("--json", is_flag=True, help="Output raw JSON instead of Rich display")]
Verbose = Annotated[bool, typer.Option("--verbose", "-v", is_flag=True, help="Show detailed source info")]
IncludeFailed = Annotated[
    bool, typer.Option("--include-failed", is_flag=True, help="Include failed sources in output")
]
OutputFile = Annotated[
    Path | None,
    typer.Option("--output", "-o", help="Write output to file instead of (or in addition to) stdout"),
]

_DEFAULT_SEARXNG = "http://localhost:8888"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_output(text: str, output: Path | None, as_json: bool) -> None:
    if output is not None:
        output.write_text(text, encoding="utf-8")
        if not as_json:
            console.print(f"\n[dim]Saved to {output}[/dim]")


def _make_http_client(timeout: float) -> httpx.AsyncClient:
    """Create a tuned AsyncClient with HTTP/2, keep-alive and granular timeouts."""
    return httpx.AsyncClient(
        http2=True,
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        timeout=httpx.Timeout(connect=3.0, read=timeout, write=5.0, pool=5.0),
    )


def _build_engine(
    searxng_url: str,
    timeout: float,
    config: ContextSearchConfig,
    http_client: httpx.AsyncClient,
    *,
    use_cache: bool = True,
) -> ContextSearchEngine:
    provider: object = SearXNGProvider(
        base_url=searxng_url, http_client=http_client, timeout=config.searxng_timeout_seconds
    )
    from llm_context_search.fetch.fetcher import PageFetcher

    fetcher: object = PageFetcher(http_client=http_client, config=config.to_fetch_config())

    if use_cache:
        provider = CachedSearchProvider(provider, ttl_seconds=config.search_cache_ttl_seconds)
        fetcher = CachedPageFetcher(fetcher, ttl_seconds=config.fetch_cache_ttl_seconds)

    return ContextSearchEngine(provider=provider, config=config, http_client=http_client, fetcher=fetcher)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search query")],
    searxng_url: SearxngUrl = _DEFAULT_SEARXNG,
    language: Language = "en",
    max_results: MaxResults = 10,
    timeout: Timeout = 10.0,
    no_cache: NoCache = False,
    as_json: AsJson = False,
    output: OutputFile = None,
) -> None:
    """Search via SearXNG and display results (no page fetching)."""

    async def _run() -> None:
        config = ContextSearchConfig(max_results=max_results, fetch_timeout_seconds=timeout)
        async with _make_http_client(timeout) as http_client:
            engine = _build_engine(searxng_url, timeout, config, http_client, use_cache=not no_cache)
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as p:
                p.add_task("Searching…")
                results = await engine.search(query, language=language, max_results=max_results)

        if as_json:
            payload = json.dumps([r.model_dump() for r in results], indent=2, ensure_ascii=False)
            if output:
                _write_output(payload, output, as_json=True)
            else:
                print(payload)
            return

        table = Table(title=f'Search: "{query}"', show_lines=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Title", style="bold")
        table.add_column("URL", style="cyan", no_wrap=False)
        table.add_column("Snippet", no_wrap=False)

        for r in results:
            table.add_row(
                str(r.rank or ""),
                r.title,
                r.url,
                (r.snippet or "")[:120],
            )
        console.print(table)

        if output:
            lines = [f"{r.rank}. {r.title}\n   {r.url}\n   {r.snippet or ''}" for r in results]
            _write_output("\n\n".join(lines), output, as_json=False)

    asyncio.run(_run())


@app.command()
def collect(
    query: Annotated[str, typer.Argument(help="Search query")],
    searxng_url: SearxngUrl = _DEFAULT_SEARXNG,
    language: Language = "en",
    max_results: MaxResults = 10,
    max_sources: MaxSources = 5,
    timeout: Timeout = 10.0,
    no_cache: NoCache = False,
    as_json: AsJson = False,
    verbose: Verbose = False,
    include_failed: IncludeFailed = False,
    output: OutputFile = None,
) -> None:
    """Search, fetch and extract sources – shows source status."""

    async def _run() -> None:
        config = ContextSearchConfig(
            max_results=max_results,
            max_sources=max_sources,
            fetch_timeout_seconds=timeout,
        )
        async with _make_http_client(timeout) as http_client:
            engine = _build_engine(searxng_url, timeout, config, http_client, use_cache=not no_cache)
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as p:
                p.add_task("Searching & fetching…")
                collection = await engine.collect_sources(
                    query, language=language, max_results=max_results, max_sources=max_sources
                )

        if as_json:
            payload = collection.model_dump_json(indent=2)
            if output:
                _write_output(payload, output, as_json=True)
            else:
                print(payload)
            return

        sources = collection.sources if include_failed else [s for s in collection.sources if s.fetch_status != "skipped"]

        table = Table(title=f'Sources: "{query}"', show_lines=True)
        table.add_column("Title", style="bold")
        table.add_column("Fetch", width=8)
        table.add_column("Extract", width=8)
        table.add_column("Chars", width=8, justify="right")
        table.add_column("Score", width=7, justify="right")
        if verbose:
            table.add_column("URL", style="cyan", no_wrap=False)

        for s in sources:
            fetch_style = "green" if s.fetch_status == "ok" else "red"
            extract_style = "green" if s.extraction_status == "ok" else ("yellow" if s.extraction_status == "empty" else "red")
            row = [
                s.title,
                f"[{fetch_style}]{s.fetch_status}[/{fetch_style}]",
                f"[{extract_style}]{s.extraction_status}[/{extract_style}]",
                str(s.extracted_chars),
                f"{s.quality_score:.2f}",
            ]
            if verbose:
                row.append(s.url)
            table.add_row(*row)

        console.print(table)
        _print_stats(collection.stats)

        if output:
            _write_output(collection.model_dump_json(indent=2), output, as_json=False)

    asyncio.run(_run())


@app.command()
def build(
    query: Annotated[str, typer.Argument(help="Search query")],
    searxng_url: SearxngUrl = _DEFAULT_SEARXNG,
    language: Language = "en",
    max_results: MaxResults = 10,
    max_sources: MaxSources = 5,
    max_passages: MaxPassages = 12,
    budget: Budget = 4000,
    timeout: Timeout = 10.0,
    no_cache: NoCache = False,
    as_json: AsJson = False,
    verbose: Verbose = False,
    output: OutputFile = None,
) -> None:
    """Full pipeline: search → fetch → extract → rank → pack context."""

    async def _run() -> None:
        config = ContextSearchConfig(
            max_results=max_results,
            max_sources=max_sources,
            max_passages=max_passages,
            budget_tokens=budget,
            fetch_timeout_seconds=timeout,
        )
        async with _make_http_client(timeout) as http_client:
            engine = _build_engine(searxng_url, timeout, config, http_client, use_cache=not no_cache)
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as p:
                p.add_task("Building context…")
                bundle = await engine.build_context(
                    query,
                    language=language,
                    max_results=max_results,
                    max_sources=max_sources,
                    max_passages=max_passages,
                    budget_tokens=budget,
                )

        if as_json:
            payload = bundle.model_dump_json(indent=2)
            if output:
                _write_output(payload, output, as_json=True)
            else:
                print(payload)
            return

        if verbose:
            src_table = Table(title="Sources", show_lines=True)
            src_table.add_column("Title", style="bold")
            src_table.add_column("Fetch", width=8)
            src_table.add_column("Extract", width=8)
            src_table.add_column("Chars", width=8, justify="right")
            src_table.add_column("Score", width=7, justify="right")
            src_table.add_column("URL", style="cyan")
            for s in bundle.sources:
                fetch_style = "green" if s.fetch_status == "ok" else "red"
                extract_style = "green" if s.extraction_status == "ok" else ("yellow" if s.extraction_status == "empty" else "red")
                src_table.add_row(
                    s.title,
                    f"[{fetch_style}]{s.fetch_status}[/{fetch_style}]",
                    f"[{extract_style}]{s.extraction_status}[/{extract_style}]",
                    str(s.extracted_chars),
                    f"{s.quality_score:.2f}",
                    s.url,
                )
            console.print(src_table)

        console.print(Panel(bundle.context_text, title=f'Context: "{query}"', border_style="blue"))
        _print_stats(bundle.stats)

        if output:
            _write_output(bundle.context_text, output, as_json=False)

    asyncio.run(_run())


def _print_stats(stats: object) -> None:
    from llm_context_search.models import RetrievalStats

    if not isinstance(stats, RetrievalStats):
        return

    rprint(
        f"[dim]Stats: {stats.search_results_count} results → "
        f"{stats.unique_urls_count} unique → "
        f"{stats.fetched_count} fetched "
        f"({stats.failed_fetch_count} failed) → "
        f"{stats.extracted_count} extracted → "
        f"{stats.passages_count} passages → "
        f"{stats.selected_passages_count} selected | "
        f"~{stats.token_estimate} tokens | "
        f"{stats.elapsed_ms} ms[/dim]"
    )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
