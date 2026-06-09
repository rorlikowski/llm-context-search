from __future__ import annotations

from typing import Protocol, runtime_checkable

from llm_context_search.models import Passage


@runtime_checkable
class ContextPacker(Protocol):
    def pack(self, passages: list[Passage], budget_tokens: int, max_passages: int) -> tuple[str, list[Passage]]: ...
