from __future__ import annotations

import ipaddress
import socket

_ALLOWED_SCHEMES = frozenset({"http", "https"})
_BLOCKED_SCHEMES = frozenset({"file", "ftp", "gopher", "data", "javascript"})

_PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


class UnsafeURLError(ValueError):
    pass


def validate_url_scheme(url: str) -> None:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme in _BLOCKED_SCHEMES:
        raise UnsafeURLError(f"Blocked scheme: {scheme!r}")
    if scheme not in _ALLOWED_SCHEMES:
        raise UnsafeURLError(f"Unsupported scheme: {scheme!r}")


def validate_no_private_ip(url: str) -> None:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        raise UnsafeURLError("No host in URL")

    if host.lower() in ("localhost",):
        raise UnsafeURLError(f"Blocked host: {host!r}")

    try:
        addr_info = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return

    for _, _, _, _, sockaddr in addr_info:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        for network in _PRIVATE_NETWORKS:
            if ip in network:
                raise UnsafeURLError(f"Private/loopback IP blocked: {ip_str}")


def validate_url_is_safe(url: str, *, block_private_ips: bool = True) -> None:
    validate_url_scheme(url)
    if block_private_ips:
        validate_no_private_ip(url)
