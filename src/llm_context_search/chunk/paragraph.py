from __future__ import annotations

import uuid

from llm_context_search.models import Passage, SourceDocument
from llm_context_search.utils.tokens import estimate_tokens


def _split_paragraphs(text: str) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n")]
    return [p for p in paragraphs if p]


def _trim_to_word_boundary(text: str) -> str:
    """Trim leading characters up to the first whitespace so overlap never starts mid-word."""
    for i, ch in enumerate(text):
        if ch.isspace():
            return text[i:].lstrip()
    return text


def _make_overlap(chunk_text: str, overlap_chars: int) -> str:
    raw = chunk_text[-overlap_chars:]
    return _trim_to_word_boundary(raw)


def _chunk_text(text: str, *, target_chars: int, max_chars: int, overlap_chars: int) -> list[str]:
    paragraphs = _split_paragraphs(text)
    chunks: list[str] = []
    # pending_overlap carries trimmed tail text from the previous chunk to
    # prepend to the start of the next real chunk — it is NEVER emitted alone.
    pending_overlap: str = ""
    current: list[str] = []
    current_len = 0

    def _flush() -> str:
        raw = "\n\n".join(current)
        if pending_overlap:
            return pending_overlap + "\n\n" + raw
        return raw

    for paragraph in paragraphs:
        para_len = len(paragraph)

        if current_len + para_len > max_chars and current:
            chunks.append(_flush())
            pending_overlap = _make_overlap("\n\n".join(current), overlap_chars) if overlap_chars > 0 else ""
            current = []
            current_len = 0

        current.append(paragraph)
        current_len += para_len

        if current_len >= target_chars:
            chunks.append(_flush())
            pending_overlap = _make_overlap("\n\n".join(current), overlap_chars) if overlap_chars > 0 else ""
            current = []
            current_len = 0

    # Emit the last real chunk only if it has substantial content beyond the overlap.
    if current:
        final = _flush()
        # Skip if the final chunk is essentially just the overlap tail (no new content).
        if len(final) > (len(pending_overlap) + 50) or not pending_overlap:
            chunks.append(final)

    return chunks


class ParagraphChunker:
    """
    Splits SourceDocument.extracted_text into Passage objects.
    Groups paragraphs up to target_chars, never exceeds max_chars,
    and adds a small text overlap between adjacent chunks.
    """

    def __init__(self, target_chars: int = 1200, max_chars: int = 2000, overlap_chars: int = 150) -> None:
        self.target_chars = target_chars
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def chunk(self, source: SourceDocument) -> list[Passage]:
        if not source.extracted_text:
            return []

        texts = _chunk_text(
            source.extracted_text,
            target_chars=self.target_chars,
            max_chars=self.max_chars,
            overlap_chars=self.overlap_chars,
        )

        passages: list[Passage] = []
        for position, text in enumerate(texts):
            char_count = len(text)
            passages.append(
                Passage(
                    id=str(uuid.uuid4()),
                    source_url=source.url,
                    source_title=source.title,
                    text=text,
                    position=position,
                    char_count=char_count,
                    token_estimate=estimate_tokens(text),
                )
            )

        return passages
