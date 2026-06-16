# Installation

## Requirements

- Python **3.11+**
- A running **SearXNG** instance (self-hosted)

---

## 1. Install the package

=== "pip"

    ```bash
    pip install llm-context-search
    ```

=== "uv"

    ```bash
    uv add llm-context-search
    ```

=== "From source"

    ```bash
    git clone https://github.com/rorlikowski/llm-context-search.git
    cd llm-context-search
    uv sync
    ```

---

## 2. Start SearXNG

The engine uses [SearXNG](https://searxng.github.io/searxng/) as its search provider. The repository includes a ready-to-use Docker Compose setup.

```bash
docker compose up -d
```

This starts SearXNG on `http://localhost:8888`.

### Enable JSON format

Edit `searxng/settings.yml` and make sure JSON is in the formats list:

```yaml title="searxng/settings.yml"
search:
  formats:
    - html
    - json
```

Restart after editing:

```bash
docker compose restart searxng
```

### Verify

```bash
curl "http://localhost:8888/search?q=test&format=json" | python3 -m json.tool | head -20
```

You should see JSON search results.

---

## 3. Verify the install

```bash
llm-context --help
llm-context-mcp --help
```

---

## Using an external SearXNG instance

If you have SearXNG running elsewhere, pass its URL via the `--searxng-url` flag or the `SEARXNG_URL` environment variable:

```bash
export SEARXNG_URL=https://searxng.example.com
llm-context build "my query"
```

!!! warning "Public instances"
    Do not use public SearXNG instances in production - they have rate limits and your queries will be logged. Self-host for privacy and reliability.
