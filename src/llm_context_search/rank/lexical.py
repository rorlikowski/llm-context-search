from __future__ import annotations

from llm_context_search.models import Passage, SourceDocument
from llm_context_search.utils.text import contains_any, tokenize


def _score_passage(query: str, passage: Passage, source: SourceDocument) -> Passage:
    """
    Lexical scoring per PRD §21:
      lexical_score =
        0.50 * query_term_coverage_in_passage
      + 0.20 * query_term_frequency_score
      + 0.15 * title_match_score
      + 0.15 * snippet_match_score

      final_score =
        0.75 * lexical_score
      + 0.25 * source_quality_score
    """
    query_terms = set(tokenize(query))
    passage_tokens = tokenize(passage.text)
    passage_term_set = set(passage_tokens)

    coverage = len(query_terms & passage_term_set) / len(query_terms) if query_terms else 0.0

    frequency = sum(1 for t in passage_tokens if t in query_terms)
    frequency_score = min(frequency / 10, 1.0)

    title_score = 1.0 if contains_any(source.title, query_terms) else 0.0
    snippet_score = 1.0 if source.snippet and contains_any(source.snippet, query_terms) else 0.0

    lexical_score = 0.50 * coverage + 0.20 * frequency_score + 0.15 * title_score + 0.15 * snippet_score

    final_score = 0.75 * lexical_score + 0.25 * source.quality_score

    passage.lexical_score = round(min(max(lexical_score, 0.0), 1.0), 6)
    passage.source_quality_score = round(source.quality_score, 6)
    passage.final_score = round(min(max(final_score, 0.0), 1.0), 6)

    return passage


class LexicalRanker:
    """
    Ranks passages by lexical relevance to the query.
    Returns passages sorted by final_score descending.
    """

    def rank(self, query: str, passages: list[Passage], sources: dict[str, SourceDocument]) -> list[Passage]:
        scored = [_score_passage(query, p, sources[p.source_url]) for p in passages if p.source_url in sources]
        return sorted(scored, key=lambda p: p.final_score, reverse=True)
