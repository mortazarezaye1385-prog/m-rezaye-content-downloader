"""Pure helpers for reading engine metadata honestly."""

from __future__ import annotations

from math import gcd
from typing import Any

from app.schemas.media import Orientation

COMMON_RATIOS: list[tuple[str, float]] = [
    ("9:16", 9 / 16), ("16:9", 16 / 9), ("1:1", 1.0), ("4:5", 4 / 5), ("5:4", 5 / 4),
    ("4:3", 4 / 3), ("3:4", 3 / 4), ("21:9", 21 / 9), ("2:3", 2 / 3), ("3:2", 3 / 2),
]


def aspect_label(width: int | None, height: int | None, tolerance: float = 0.02) -> str | None:
    if not width or not height:
        return None
    ratio = width / height
    for label, value in COMMON_RATIOS:
        if abs(ratio - value) / value <= tolerance:
            return label
    g = gcd(width, height)
    return f"{width // g}:{height // g}"


def orientation_of(width: int | None, height: int | None) -> Orientation | None:
    if not width or not height:
        return None
    if abs(width - height) / max(width, height) < 0.02:
        return Orientation.SQUARE
    return Orientation.VERTICAL if height > width else Orientation.HORIZONTAL


def is_video_format(fmt: dict[str, Any]) -> bool:
    return fmt.get("vcodec") not in (None, "none") and bool(fmt.get("height"))


def is_audio_only(fmt: dict[str, Any]) -> bool:
    return fmt.get("vcodec") in (None, "none") and fmt.get("acodec") not in (None, "none")


def is_drm(fmt: dict[str, Any]) -> bool:
    return bool(fmt.get("has_drm"))


def format_bytes(fmt: dict[str, Any]) -> int | None:
    value = fmt.get("filesize") or fmt.get("filesize_approx")
    return int(value) if value else None


def best_video_dimensions(info: dict[str, Any]) -> tuple[int | None, int | None]:
    formats = [f for f in info.get("formats") or [] if is_video_format(f) and not is_drm(f)]
    if formats:
        best = max(formats, key=lambda f: (f.get("height") or 0, f.get("tbr") or 0))
        return best.get("width"), best.get("height")
    return info.get("width"), info.get("height")


def best_thumbnail(info: dict[str, Any]) -> str | None:
    thumbs = [t for t in info.get("thumbnails") or [] if t.get("url")]
    if thumbs:
        best = max(thumbs, key=lambda t: ((t.get("width") or 0) * (t.get("height") or 0), t.get("preference") or 0))
        return best["url"]
    return info.get("thumbnail")
