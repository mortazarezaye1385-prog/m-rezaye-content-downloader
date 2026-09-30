"""SSRF-safe outbound HTTP helpers (JSON APIs and media streams)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import urljoin

from app.core.errors import AppError, ErrorCode
from app.security.ssrf import validate_outbound_url

MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_REDIRECTS = 3
USER_AGENT = "M.Rezaye-Content-Downloader/1.0 (personal use)"


def _httpx():
    try:
        import httpx  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise AppError(ErrorCode.PROVIDER_UNAVAILABLE, internal_detail="httpx missing") from exc
    return httpx


def _map_transport_error(exc: Exception) -> AppError:
    httpx = _httpx()
    if isinstance(exc, httpx.TimeoutException):
        return AppError(ErrorCode.UPSTREAM_TIMEOUT, internal_detail=str(exc))
    return AppError(ErrorCode.NETWORK_ERROR, internal_detail=str(exc))


async def get_json(url: str, *, params: dict[str, Any] | None, timeout: float) -> tuple[int, Any]:
    httpx = _httpx()
    validate_outbound_url(url, allow_api_hosts=True)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False, headers={"User-Agent": USER_AGENT}) as client:
            resp = await client.get(url, params=params)
    except httpx.HTTPError as exc:
        raise _map_transport_error(exc) from exc
    if len(resp.content) > MAX_JSON_BYTES:
        raise AppError(ErrorCode.RETRIEVAL_FAILED, internal_detail="json response too large")
    try:
        return resp.status_code, resp.json()
    except ValueError:
        return resp.status_code, None


async def stream_media(url: str, *, timeout: float, max_bytes: int, chunk_size: int = 256 * 1024) -> AsyncIterator[tuple[bytes, int | None, str | None]]:
    """Yield (chunk, content_length, content_type), re-validating every redirect hop."""
    httpx = _httpx()
    current = url
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False, headers={"User-Agent": USER_AGENT}) as client:
        for _ in range(MAX_REDIRECTS + 1):
            validate_outbound_url(current)
            try:
                async with client.stream("GET", current) as resp:
                    if resp.is_redirect:
                        location = resp.headers.get("location")
                        if not location:
                            raise AppError(ErrorCode.RETRIEVAL_FAILED, internal_detail="redirect without location")
                        current = urljoin(current, location)
                        continue
                    if resp.status_code == 404:
                        raise AppError(ErrorCode.CONTENT_UNAVAILABLE)
                    if resp.status_code == 429:
                        raise AppError(ErrorCode.UPSTREAM_RATE_LIMITED)
                    if resp.status_code in (401, 403):
                        raise AppError(ErrorCode.TICKET_EXPIRED, "The media link expired. Analyze the link again.")
                    if resp.status_code >= 400:
                        raise AppError(ErrorCode.RETRIEVAL_FAILED, internal_detail=f"media status {resp.status_code}")
                    length = int(resp.headers["content-length"]) if resp.headers.get("content-length", "").isdigit() else None
                    if length and length > max_bytes:
                        raise AppError(ErrorCode.MEDIA_TOO_LARGE)
                    ctype = resp.headers.get("content-type")
                    received = 0
                    async for chunk in resp.aiter_bytes(chunk_size):
                        received += len(chunk)
                        if received > max_bytes:
                            raise AppError(ErrorCode.MEDIA_TOO_LARGE)
                        yield chunk, length, ctype
                    return
            except httpx.HTTPError as exc:
                raise _map_transport_error(exc) from exc
        raise AppError(ErrorCode.RETRIEVAL_FAILED, internal_detail="too many redirects")
