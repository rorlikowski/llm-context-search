from __future__ import annotations

from llm_context_search.models import ExtractedContent


class TrafilaturaExtractor:
    """
    Primary content extractor using trafilatura.
    Strips navigation, ads, headers, footers and returns main text + metadata.
    Uses bare_extraction for a single parse pass (text + metadata together).
    trafilatura is imported lazily to keep CLI cold-start fast.
    """

    def extract(self, html: str, *, url: str | None = None) -> ExtractedContent:
        import trafilatura  # noqa: PLC0415

        try:
            doc = trafilatura.bare_extraction(
                html,
                url=url,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
                with_metadata=True,
            )
            if doc is None:
                return ExtractedContent()
            return ExtractedContent(
                title=doc.title or None,
                text=doc.text or None,
                author=doc.author or None,
                date=doc.date or None,
                language=doc.language or None,
                description=doc.description or None,
            )
        except Exception:
            return ExtractedContent()
