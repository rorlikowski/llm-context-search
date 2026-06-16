import pytest

from llm_context_search.chunk.paragraph import ParagraphChunker
from llm_context_search.models import SourceDocument


def _source(text: str) -> SourceDocument:
    return SourceDocument(
        title="Test",
        url="https://example.com",
        normalized_url="https://example.com",
        provider="fake",
        fetch_status="ok",
        extraction_status="ok",
        extracted_text=text,
        extracted_chars=len(text),
    )


def test_empty_source_returns_no_passages() -> None:
    chunker = ParagraphChunker()
    source = _source("")
    source.extracted_text = None
    assert chunker.chunk(source) == []


def test_short_text_produces_single_passage() -> None:
    chunker = ParagraphChunker(target_chars=1200, max_chars=2000, overlap_chars=0)
    source = _source("Hello world.\n\nThis is a test.")
    passages = chunker.chunk(source)
    assert len(passages) == 1
    assert "Hello world" in passages[0].text


def test_long_text_produces_multiple_passages() -> None:
    paragraph = "word " * 100  # ~500 chars per paragraph
    text = "\n\n".join([paragraph] * 10)  # ~5000 chars total
    chunker = ParagraphChunker(target_chars=600, max_chars=1200, overlap_chars=0)
    source = _source(text)
    passages = chunker.chunk(source)
    assert len(passages) > 1


def test_passage_chars_match_text_length() -> None:
    chunker = ParagraphChunker(target_chars=500, max_chars=1000, overlap_chars=0)
    source = _source("paragraph one.\n\nparagraph two.\n\nparagraph three.")
    passages = chunker.chunk(source)
    for p in passages:
        assert p.char_count == len(p.text)


def test_passage_has_source_metadata() -> None:
    chunker = ParagraphChunker()
    source = _source("Some text content here.")
    passages = chunker.chunk(source)
    assert passages[0].source_url == "https://example.com"
    assert passages[0].source_title == "Test"


def test_passage_positions_are_sequential() -> None:
    paragraph = "word " * 100
    text = "\n\n".join([paragraph] * 8)
    chunker = ParagraphChunker(target_chars=600, max_chars=1200, overlap_chars=0)
    passages = chunker.chunk(_source(text))
    positions = [p.position for p in passages]
    assert positions == list(range(len(passages)))


@pytest.mark.parametrize("overlap", [0, 100, 200])
def test_overlap_does_not_crash(overlap: int) -> None:
    paragraph = "word " * 80
    text = "\n\n".join([paragraph] * 6)
    chunker = ParagraphChunker(target_chars=500, max_chars=1000, overlap_chars=overlap)
    passages = chunker.chunk(_source(text))
    assert len(passages) >= 1
