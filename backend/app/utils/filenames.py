"""Filename helpers for Content-Disposition. Never used for filesystem paths."""

from __future__ import annotations

import re
import unicodedata
from urllib.parse import quote

_ALLOWED_EXT = re.compile(r"^[a-z0-9]{2,5}$")


def safe_extension(ext: str | None, fallback: str = "bin") -> str:
    ext = (ext or "").lower().lstrip(".")
    return ext if _ALLOWED_EXT.match(ext) else fallback


def slugify_title(title: str | None, fallback: str = "media", max_length: int = 60) -> str:
    text = unicodedata.normalize("NFKD", title or "").encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return (text[:max_length].rstrip("-")) or fallback


def build_download_name(platform: str, title: str | None, ext: str | None, index: int | None = None) -> str:
    stem = f"mr-{platform}-{slugify_title(title)}"
    if index is not None:
        stem += f"-{index + 1:02d}"
    return f"{stem}.{safe_extension(ext)}"


def content_disposition(filename: str) -> str:
    ascii_name = re.sub(r'[^A-Za-z0-9._-]', "_", filename) or "download"
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"
