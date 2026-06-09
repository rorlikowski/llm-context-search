from __future__ import annotations

from llm_context_search.models import SearchResult
from llm_context_search.normalize.urls import normalize_url


def deduplicate_results(results: list[SearchResult]) -> list[SearchResult]:
    """
    Remove duplicate search results based on normalized URL.
    Preserves the first occurrence and mutates `normalized_url` on each result.
    """
    seen: set[str] = set()
    unique: list[SearchResult] = []

    for result in results:
        key = normalize_url(result.url)
        if key in seen:
            continue
        seen.add(key)
        result.normalized_url = key
        unique.append(result)

    return unique
