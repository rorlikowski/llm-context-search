from llm_context_search.models import Passage
from llm_context_search.pack.markdown import MarkdownPacker


def _passage(text: str, score: float = 0.5, url: str = "https://example.com") -> Passage:
    return Passage(
        id="test-id",
        source_url=url,
        source_title="Test Source",
        text=text,
        position=0,
        char_count=len(text),
        token_estimate=len(text) // 4,
        final_score=score,
        lexical_score=score,
        source_quality_score=score,
    )


def test_empty_passages_returns_empty_string() -> None:
    packer = MarkdownPacker()
    context, selected = packer.pack([], budget_tokens=4000, max_passages=12)
    assert context == ""
    assert selected == []


def test_single_passage_always_included() -> None:
    packer = MarkdownPacker()
    p = _passage("Hello world. " * 10)
    context, selected = packer.pack([p], budget_tokens=1, max_passages=12)
    assert len(selected) == 1
    assert "Hello world" in context


def test_respects_max_passages_limit() -> None:
    packer = MarkdownPacker()
    passages = [_passage(f"Passage {i}. " * 20, score=1.0 - i * 0.01) for i in range(10)]
    _, selected = packer.pack(passages, budget_tokens=100_000, max_passages=3)
    assert len(selected) == 3


def test_respects_token_budget() -> None:
    packer = MarkdownPacker()
    long_text = "word " * 400  # ~2000 chars ≈ 500 tokens
    passages = [_passage(long_text, score=1.0 - i * 0.01) for i in range(5)]
    _, selected = packer.pack(passages, budget_tokens=600, max_passages=10)
    # First passage always included; subsequent ones must fit
    assert len(selected) <= 3


def test_context_contains_source_header() -> None:
    packer = MarkdownPacker()
    p = _passage("Some relevant content.", url="https://example.com")
    context, _ = packer.pack([p], budget_tokens=4000, max_passages=12)
    assert "# Source 1:" in context
    assert "https://example.com" in context


def test_passages_sorted_by_score_descending() -> None:
    packer = MarkdownPacker()
    low = _passage("low score passage", score=0.1)
    high = _passage("high score passage", score=0.9)
    _, selected = packer.pack([low, high], budget_tokens=4000, max_passages=2)
    assert selected[0].final_score >= selected[1].final_score
