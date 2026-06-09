from __future__ import annotations

from llm_context_search.models import SourceDocument
from llm_context_search.utils.text import contains_any, tokenize


class SourceQualityScorer:
    """
    Heuristic quality score for a SourceDocument.

    Score components (as per PRD §18):
      +0.20  fetch ok
      +0.20  extraction ok
      +0.15  extracted_chars > 1000
      +0.15  extracted_chars > 3000
      +0.10  https
      +0.10  title contains query terms
      +0.10  snippet contains query terms
      -0.20  extracted_chars < 500
      -0.30  fetch failed
    Clamped to [0.0, 1.0].
    """

    def score(self, source: SourceDocument, query: str) -> float:
        sc = 0.0
        query_terms = set(tokenize(query))

        if source.fetch_status == "ok":
            sc += 0.20
        if source.extraction_status == "ok":
            sc += 0.20
        if source.extracted_chars > 1000:
            sc += 0.15
        if source.extracted_chars > 3000:
            sc += 0.15
        if source.url.startswith("https://"):
            sc += 0.10
        if contains_any(source.title, query_terms):
            sc += 0.10
        if source.snippet and contains_any(source.snippet, query_terms):
            sc += 0.10
        if source.extracted_chars < 500:
            sc -= 0.20
        if source.fetch_status == "failed":
            sc -= 0.30

        return max(0.0, min(sc, 1.0))
