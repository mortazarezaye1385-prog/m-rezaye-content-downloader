"""Test doubles for the retrieval engine. No network is ever touched."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.core.errors import AppError


def make_settings(tmp: Path | None = None, **overrides: Any) -> Settings:
    base: dict[str, Any] = {"secret_key": "test-secret-key-that-is-long-enough"}
    if tmp is not None:
        base["temp_dir"] = tmp / "store"
    base.update(overrides)
    return Settings(**base)


def yt_formats() -> list[dict[str, Any]]:
    return [
        {"format_id": "sb0", "ext": "mhtml", "vcodec": "none", "acodec": "none"},
        {"format_id": "140", "ext": "m4a", "vcodec": "none", "acodec": "mp4a.40.2", "abr": 129, "filesize": 1_000},
        {"format_id": "251", "ext": "webm", "vcodec": "none", "acodec": "opus", "abr": 140, "filesize": 1_100},
        {"format_id": "137", "ext": "mp4", "vcodec": "avc1.640028", "acodec": "none", "height": 1080, "width": 1920, "fps": 30, "tbr": 4000, "filesize": 10_000},
        {"format_id": "248", "ext": "webm", "vcodec": "vp9", "acodec": "none", "height": 1080, "width": 1920, "fps": 30, "tbr": 3000, "filesize": 9_000},
        {"format_id": "299", "ext": "mp4", "vcodec": "avc1.64002a", "acodec": "none", "height": 1080, "width": 1920, "fps": 60, "tbr": 6000},
        {"format_id": "313", "ext": "webm", "vcodec": "vp9", "acodec": "none", "height": 2160, "width": 3840, "fps": 30, "tbr": 18000, "filesize": 50_000},
        {"format_id": "22", "ext": "mp4", "vcodec": "avc1.64001F", "acodec": "mp4a.40.2", "height": 720, "width": 1280, "fps": 30, "tbr": 1500, "filesize": 5_000},
        {"format_id": "drm1", "ext": "mp4", "vcodec": "avc1", "acodec": "none", "height": 4320, "width": 7680, "has_drm": True},
    ]


class FakeEngine:
    name = "fake engine"

    def __init__(self, info: dict[str, Any] | None = None, error: AppError | None = None, fail_indexes: set[int] | None = None, payload: bytes = b"x" * 2048) -> None:
        self.info = info or {}
        self.error = error
        self.fail_indexes = fail_indexes or set()
        self.payload = payload
        self.downloads: list[dict[str, Any]] = []

    def extract(self, url: str, *, platform: str, allow_playlist: bool = False) -> dict[str, Any]:
        if self.error:
            raise self.error
        return self.info

    def download(self, url, *, platform, out_dir: Path, stem, format_selector, playlist_index, merge_format, progress, cancel_event: threading.Event) -> Path:
        self.downloads.append({"url": url, "selector": format_selector, "index": playlist_index, "merge": merge_format})
        if self.error:
            raise self.error
        if playlist_index in self.fail_indexes:
            from app.core.errors import ErrorCode
            raise AppError(ErrorCode.RETRIEVAL_FAILED)
        half = len(self.payload) // 2
        progress(half, len(self.payload))
        path = out_dir / f"{stem}.{merge_format or 'mp4'}"
        path.write_bytes(self.payload)
        progress(len(self.payload), len(self.payload))
        return path
