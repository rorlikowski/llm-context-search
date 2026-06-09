from __future__ import annotations

from typing import Protocol, runtime_checkable

from llm_context_search.models import Passage, SourceDocument


@runtime_checkable
class PassageChunker(Protocol):
    def chunk(self, source: SourceDocument) -> list[Passage]: ...
