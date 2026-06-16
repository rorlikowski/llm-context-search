# Quickstart

This guide assumes you have [installed the package and started SearXNG](install.md).

---

## CLI commands

The `llm-context` CLI has three commands, each exposing a different stage of the pipeline.

### `search` - URL discovery

Searches via SearXNG and prints results. No page fetching.

```bash
llm-context search "Python asyncio best practices"
```

```bash
llm-context search "Python asyncio" --max-results 20 --json
```

### `collect` - fetch and extract

Fetches pages, extracts main content, shows per-source status.

```bash
llm-context collect "Python asyncio best practices" --max-sources 5
```

```bash
llm-context collect "Python asyncio" --verbose   # show URLs + details
```

### `build` - full pipeline

Runs the complete pipeline and returns context ready for an LLM prompt.

```bash
llm-context build "Python asyncio best practices" --budget 4000
```

```bash
# Save to file
llm-context build "Python asyncio" -o context.md

# Output JSON (for scripting)
llm-context build "Python asyncio" --json | jq .token_estimate

# Verbose: show source table + context
llm-context build "Python asyncio" --verbose --budget 6000
```

---

## Common options

All commands share these flags:

| Flag | Default | Description |
|---|---|---|
| `--searxng-url` / `-u` | `http://localhost:8888` | SearXNG base URL |
| `--language` / `-l` | `en` | Search language (`pl`, `de`, `fr`, …) |
| `--max-results` | `10` | Results fetched from SearXNG |
| `--max-sources` | `5` | Pages to fetch and extract |
| `--max-passages` | `12` | Passages included in output |
| `--budget` | `4000` | Token budget for context |
| `--timeout` | `10.0` | HTTP timeout in seconds |
| `--no-cache` | off | Disable in-memory TTL cache |
| `--json` | off | Output raw JSON |
| `--output` / `-o` | - | Write to file |
| `--verbose` / `-v` | off | Show detailed source info |

---

## Environment variables

```bash
export SEARXNG_URL=http://localhost:8888
llm-context build "my query"   # no need to pass --searxng-url
```

---

## Example: feed context to an LLM

```bash
# Build context and pipe into any LLM CLI
CONTEXT=$(llm-context build "how does Python GIL work" --budget 3000)
echo "$CONTEXT" | llm "Summarise the above in 3 bullet points"
```

Or save to a file and reference it:

```bash
llm-context build "how does Python GIL work" -o /tmp/context.md
llm -f /tmp/context.md "What are the main points?"
```
