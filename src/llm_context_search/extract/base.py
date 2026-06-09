from __future__ import annotations

from typing import Protocol, runtime_checkable

from llm_context_search.models import ExtractedContent


@runtime_checkable
class ContentExtractor(Protocol):
    def extract(self, html: str, *, url: str | None = None) -> ExtractedContent: ...
