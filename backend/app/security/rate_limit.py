"""In-memory token-bucket rate limiting (single-process, personal deployment)."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable


@dataclass
class _Bucket:
    tokens: float
    updated: float


class TokenBucketLimiter:
    def __init__(self, per_minute: int, *, burst: int | None = None, clock: Callable[[], float] = time.monotonic, max_keys: int = 10_000) -> None:
        if per_minute <= 0:
            raise ValueError("per_minute must be positive")
        self.capacity = float(burst or per_minute)
        self.rate = per_minute / 60.0
        self._clock = clock
        self._max_keys = max_keys
        self._buckets: dict[str, _Bucket] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> tuple[bool, float]:
        """Consume one token. Returns (allowed, retry_after_seconds)."""
        now = self._clock()
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                if len(self._buckets) >= self._max_keys:
                    self._prune(now)
                bucket = _Bucket(self.capacity, now)
                self._buckets[key] = bucket
            bucket.tokens = min(self.capacity, bucket.tokens + (now - bucket.updated) * self.rate)
            bucket.updated = now
            if bucket.tokens >= 1:
                bucket.tokens -= 1
                return True, 0.0
            return False, (1 - bucket.tokens) / self.rate

    def _prune(self, now: float) -> None:
        full_after = self.capacity / self.rate
        stale = [k for k, b in self._buckets.items() if now - b.updated > full_after]
        for key in stale:
            del self._buckets[key]
        if len(self._buckets) >= self._max_keys:
            self._buckets.clear()
