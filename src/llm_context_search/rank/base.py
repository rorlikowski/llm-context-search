from __future__ import annotations

from typing import Protocol, runtime_checkable

from llm_context_search.models import Passage, SourceDocument


@runtime_checkable
class SourceScorer(Protocol):
    def score(self, source: SourceDocument, query: str) -> float: ...


@runtime_checkable
class PassageRanker(Protocol):
    def rank(self, query: str, passages: list[Passage], sources: dict[str, SourceDocument]) -> list[Passage]: ...
