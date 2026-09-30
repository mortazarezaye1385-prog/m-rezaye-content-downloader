"""SSRF protection for any outbound fetch the server performs itself.

The retrieval engine only ever receives canonical platform URLs. Direct media
fetches (CDN files, preview thumbnails) must pass two checks:
1. the host is on an explicit media CDN suffix allowlist, and
2. every resolved address is a public, globally routable IP.
Redirects are followed manually so each hop is re-validated.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit

from app.core.errors import AppError, ErrorCode

MEDIA_HOST_SUFFIXES: tuple[str, ...] = (
    "cdninstagram.com",
    "fbcdn.net",
    "tiktokcdn.com",
    "tiktokcdn-us.com",
    "tiktokcdn-eu.com",
    "tiktokv.com",
    "ibyteimg.com",
    "byteimg.com",
    "ytimg.com",
    "ggpht.com",
    "googlevideo.com",
    "googleusercontent.com",
)

API_HOSTS: frozenset[str] = frozenset({"graph.instagram.com", "graph.facebook.com", "www.tiktok.com"})


def host_matches_suffix(host: str, suffixes: tuple[str, ...] = MEDIA_HOST_SUFFIXES) -> bool:
    host = host.rstrip(".").lower()
    return any(host == s or host.endswith("." + s) for s in suffixes)


def is_public_ip(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not (ip.is_multicast or ip.is_reserved or ip.is_loopback or ip.is_link_local or ip.is_private)


def resolve_host(host: str) -> list[str]:
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise AppError(ErrorCode.NETWORK_ERROR, internal_detail=f"dns failure for {host}") from exc
    return sorted({info[4][0] for info in infos})


def validate_outbound_url(url: str, *, allow_api_hosts: bool = False, resolver=resolve_host) -> str:
    """Return the URL if it is safe to fetch, else raise ``AppError``."""
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as exc:
        raise AppError(ErrorCode.RETRIEVAL_FAILED, internal_detail="unparseable media url") from exc
    host = (parts.hostname or "").rstrip(".").lower()
    if parts.scheme != "https" or not host or parts.username or parts.password or port not in (None, 443):
        raise AppError(ErrorCode.RETRIEVAL_FAILED, internal_detail=f"rejected media url scheme/host: {host}")
    allowed = host_matches_suffix(host) or (allow_api_hosts and host in API_HOSTS)
    if not allowed:
        raise AppError(ErrorCode.RETRIEVAL_FAILED, internal_detail=f"media host not allowlisted: {host}")
    try:
        ipaddress.ip_address(host)
        raise AppError(ErrorCode.RETRIEVAL_FAILED, internal_detail="ip literal media host")
    except ValueError:
        pass
    addresses = resolver(host)
    if not addresses or not all(is_public_ip(a) for a in addresses):
        raise AppError(ErrorCode.RETRIEVAL_FAILED, internal_detail=f"non-public address for {host}")
    return url
