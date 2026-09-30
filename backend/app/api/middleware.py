"""Request id, security headers, body-size limit and rate limiting (pure ASGI)."""

from __future__ import annotations

import json
import re
import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import AppError, ErrorCode
from app.security.rate_limit import TokenBucketLimiter

SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (b"permissions-policy", b"camera=(), microphone=(), geolocation=(), interest-cohort=()"),
    (b"cross-origin-opener-policy", b"same-origin"),
    (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'"),
]

_REQUEST_ID = re.compile(r"^[A-Za-z0-9-]{8,64}$")


def route_group(path: str, method: str) -> str:
    if method == "POST" and (path.endswith("/analyze") or path.endswith("/highlight") or path.endswith("/caption")):
        return "analyze"
    if method == "POST" and path.rstrip("/") == "/api/downloads":
        return "download"
    return "general"


async def _send_json(send: Send, status: int, body: dict, headers: list[tuple[bytes, bytes]]) -> None:
    raw = json.dumps(body).encode("utf-8")
    await send({"type": "http.response.start", "status": status, "headers": headers + [(b"content-type", b"application/json"), (b"content-length", str(len(raw)).encode())]})
    await send({"type": "http.response.body", "body": raw})


class GuardMiddleware:
    def __init__(self, app: ASGIApp, *, limiters: dict[str, TokenBucketLimiter], max_body_bytes: int, trust_proxy: bool, hsts: bool) -> None:
        self.app = app
        self.limiters = limiters
        self.max_body = max_body_bytes
        self.trust_proxy = trust_proxy
        self.hsts = hsts

    def _client_ip(self, scope: Scope) -> str:
        headers = dict(scope.get("headers") or [])
        if self.trust_proxy and b"x-forwarded-for" in headers:
            return headers[b"x-forwarded-for"].decode("latin-1").split(",")[0].strip()
        client = scope.get("client")
        return client[0] if client else "unknown"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        incoming = headers.get(b"x-request-id", b"").decode("latin-1")
        request_id = incoming if _REQUEST_ID.match(incoming) else uuid.uuid4().hex[:16]
        scope.setdefault("state", {})["request_id"] = request_id

        extra = list(SECURITY_HEADERS) + [(b"x-request-id", request_id.encode())]
        if self.hsts:
            extra.append((b"strict-transport-security", b"max-age=63072000; includeSubDomains"))

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                existing = {k.lower() for k, _ in message.get("headers", [])}
                message["headers"] = list(message.get("headers", [])) + [h for h in extra if h[0] not in existing]
            await send(message)

        # Rate limit
        group = route_group(scope.get("path", ""), scope.get("method", "GET"))
        limiter = self.limiters.get(group)
        if limiter:
            allowed, retry_after = limiter.check(f"{group}:{self._client_ip(scope)}")
            if not allowed:
                err = AppError(ErrorCode.RATE_LIMITED)
                await _send_json(send, 429, err.to_payload(request_id), extra + [(b"retry-after", str(int(retry_after) + 1).encode())])
                return

        # Body size limit (declared + streamed)
        declared = headers.get(b"content-length")
        if declared and declared.isdigit() and int(declared) > self.max_body:
            await _send_json(send, 413, AppError(ErrorCode.REQUEST_TOO_LARGE).to_payload(request_id), extra)
            return

        received = 0

        async def receive_wrapper() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_body:
                    raise AppError(ErrorCode.REQUEST_TOO_LARGE)
            return message

        await self.app(scope, receive_wrapper, send_wrapper)
