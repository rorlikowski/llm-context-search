from llm_context_search.normalize.urls import normalize_url


def test_strips_trailing_slash() -> None:
    assert normalize_url("https://example.com/page/") == "https://example.com/page"


def test_lowercases_host() -> None:
    assert normalize_url("https://Example.COM/path") == "https://example.com/path"


def test_strips_tracking_params() -> None:
    url = "https://example.com/page?utm_source=google&utm_medium=cpc&id=42"
    normalized = normalize_url(url)
    assert "utm_source" not in normalized
    assert "utm_medium" not in normalized
    assert "id=42" in normalized


def test_strips_fragment() -> None:
    assert normalize_url("https://example.com/page#section") == "https://example.com/page"


def test_removes_default_https_port() -> None:
    assert normalize_url("https://example.com:443/page") == "https://example.com/page"


def test_removes_default_http_port() -> None:
    assert normalize_url("http://example.com:80/page") == "http://example.com/page"


def test_keeps_non_default_port() -> None:
    assert normalize_url("https://example.com:8080/page") == "https://example.com:8080/page"


def test_root_path_becomes_empty() -> None:
    result = normalize_url("https://example.com/")
    assert result == "https://example.com"


def test_strips_multiple_tracking_params() -> None:
    url = "https://example.com/?fbclid=abc&gclid=def&q=hello"
    normalized = normalize_url(url)
    assert "fbclid" not in normalized
    assert "gclid" not in normalized
    assert "q=hello" in normalized
