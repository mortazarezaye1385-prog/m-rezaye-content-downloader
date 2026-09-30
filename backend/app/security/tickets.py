"""Stateless, signed, short-lived tickets.

Analysis responses hand the browser opaque tickets for downloads and previews.
The server later only acts on tickets it signed itself, so a client can never
ask the server to fetch an arbitrary URL. No database is involved.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Callable

from app.core.errors import AppError, ErrorCode


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64d(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class TicketSigner:
    def __init__(self, secret: str, clock: Callable[[], float] = time.time) -> None:
        if len(secret) < 16:
            raise ValueError("secret key must be at least 16 characters")
        self._key = hashlib.sha256(secret.encode("utf-8")).digest()
        self._clock = clock

    def _sig(self, body: str, purpose: str) -> str:
        mac = hmac.new(self._key, f"{purpose}.{body}".encode("ascii"), hashlib.sha256)
        return _b64e(mac.digest())

    def sign(self, payload: dict[str, Any], *, purpose: str, ttl_seconds: int) -> str:
        data = dict(payload)
        data["exp"] = int(self._clock()) + ttl_seconds
        body = _b64e(json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8"))
        return f"{body}.{self._sig(body, purpose)}"

    def verify(self, token: str, *, purpose: str) -> dict[str, Any]:
        if not token or len(token) > 48 * 1024 or token.count(".") != 1:
            raise AppError(ErrorCode.INVALID_TICKET)
        body, sig = token.split(".")
        if not hmac.compare_digest(sig, self._sig(body, purpose)):
            raise AppError(ErrorCode.INVALID_TICKET)
        try:
            data = json.loads(_b64d(body))
        except (ValueError, json.JSONDecodeError) as exc:
            raise AppError(ErrorCode.INVALID_TICKET) from exc
        if not isinstance(data, dict) or int(data.get("exp", 0)) < int(self._clock()):
            raise AppError(ErrorCode.TICKET_EXPIRED)
        return data
