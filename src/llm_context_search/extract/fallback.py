from __future__ import annotations

from bs4 import BeautifulSoup

from llm_context_search.models import ExtractedContent

_NOISE_TAGS = ["script", "style", "nav", "footer", "header", "aside", "form", "noscript"]
_MAX_CHARS = 50_000


class FallbackExtractor:
    """
    BeautifulSoup-based fallback extractor.
    Strips noise tags and returns plain text.
    """

    def extract(self, html: str, *, url: str | None = None) -> ExtractedContent:
        try:
            soup = BeautifulSoup(html, "html.parser")

            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else None

            for tag in soup(_NOISE_TAGS):
                tag.decompose()

            lines = [line.strip() for line in soup.get_text("\n").splitlines()]
            text = "\n".join(line for line in lines if line)

            if not text:
                return ExtractedContent(title=title)

            return ExtractedContent(title=title, text=text[:_MAX_CHARS])
        except Exception:
            return ExtractedContent()
