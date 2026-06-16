from llm_context_search.dedupe.urls import deduplicate_results
from llm_context_search.models import SearchResult


def _result(url: str, rank: int = 1) -> SearchResult:
    return SearchResult(title="Title", url=url, provider="fake", rank=rank)


def test_removes_exact_duplicates() -> None:
    results = [_result("https://example.com/page", 1), _result("https://example.com/page", 2)]
    unique = deduplicate_results(results)
    assert len(unique) == 1
    assert unique[0].rank == 1


def test_removes_trailing_slash_duplicates() -> None:
    results = [_result("https://example.com/page/", 1), _result("https://example.com/page", 2)]
    unique = deduplicate_results(results)
    assert len(unique) == 1


def test_removes_tracking_param_duplicates() -> None:
    results = [
        _result("https://example.com/page?utm_source=google", 1),
        _result("https://example.com/page", 2),
    ]
    unique = deduplicate_results(results)
    assert len(unique) == 1


def test_keeps_distinct_urls() -> None:
    results = [_result("https://example.com/a"), _result("https://example.com/b")]
    unique = deduplicate_results(results)
    assert len(unique) == 2


def test_sets_normalized_url_on_result() -> None:
    results = [_result("https://example.com/page?utm_source=x")]
    unique = deduplicate_results(results)
    assert unique[0].normalized_url == "https://example.com/page"


def test_empty_list_returns_empty() -> None:
    assert deduplicate_results([]) == []
