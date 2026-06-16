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
                title=getattr(doc, "title", None) or None,
                text=getattr(doc, "text", None) or None,
                author=getattr(doc, "author", None) or None,
                date=getattr(doc, "date", None) or None,
                language=getattr(doc, "language", None) or None,
                description=getattr(doc, "description", None) or None,
            )
        except Exception:
            return ExtractedContent()
