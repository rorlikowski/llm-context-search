from __future__ import annotations

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

_TRACKING_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
        "mc_cid",
        "mc_eid",
        "ref",
        "ref_src",
    }
)

_DEFAULT_PORTS = {
    "http": 80,
    "https": 443,
}


def normalize_url(url: str) -> str:
    """
    Normalize a URL for deduplication:
    - lowercase scheme and host
    - strip fragment
    - strip tracking query params
    - remove default ports (:80, :443)
    - remove trailing slash from path
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return url

    scheme = parsed.scheme.lower()
    netloc = parsed.hostname or ""

    port = parsed.port
    default = _DEFAULT_PORTS.get(scheme)
    if port is not None and port != default:
        netloc = f"{netloc}:{port}"

    path = parsed.path.rstrip("/") or "/"
    if path == "/":
        path = ""

    query_params = parse_qs(parsed.query, keep_blank_values=True)
    filtered = {k: v for k, v in query_params.items() if k.lower() not in _TRACKING_PARAMS}
    query = urlencode(filtered, doseq=True) if filtered else ""

    normalized = urlunparse((scheme, netloc, path, "", query, ""))
    return normalized
