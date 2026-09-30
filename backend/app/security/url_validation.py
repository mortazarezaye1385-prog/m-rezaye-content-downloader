"""Strict URL allowlisting, platform detection and canonicalisation.

User input never reaches the retrieval layer directly. It is parsed, checked
against an exact host allowlist, classified by path, and rebuilt into a
canonical URL. Anything that doesn't match a known shape is rejected.
"""

from __future__ import annotations

import base64
import binascii
import re
from dataclasses import dataclass
from enum import Enum
from urllib.parse import parse_qs, urlsplit

from app.core.errors import AppError, ErrorCode

MAX_URL_LENGTH = 2048


class Platform(str, Enum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"


PLATFORM_NAMES = {"instagram": "Instagram", "tiktok": "TikTok", "youtube": "YouTube"}


class UrlKind(str, Enum):
    INSTAGRAM_POST = "instagram_post"
    INSTAGRAM_REEL = "instagram_reel"
    INSTAGRAM_HIGHLIGHT = "instagram_highlight"
    INSTAGRAM_STORY = "instagram_story"
    TIKTOK_VIDEO = "tiktok_video"
    TIKTOK_PHOTO = "tiktok_photo"
    TIKTOK_SHORT_LINK = "tiktok_short_link"
    YOUTUBE_VIDEO = "youtube_video"
    YOUTUBE_SHORT = "youtube_short"


PLATFORM_HOSTS: dict[Platform, frozenset[str]] = {
    Platform.INSTAGRAM: frozenset({"instagram.com", "www.instagram.com", "m.instagram.com"}),
    Platform.TIKTOK: frozenset({"tiktok.com", "www.tiktok.com", "m.tiktok.com", "vm.tiktok.com", "vt.tiktok.com"}),
    Platform.YOUTUBE: frozenset({"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}),
}

_IG_CODE = r"[A-Za-z0-9_-]{5,64}"
_IG_USER = r"[A-Za-z0-9._]{1,30}"
_YT_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_TT_USER = r"[A-Za-z0-9._]{2,64}"

_IG_POST = re.compile(rf"^/(?:{_IG_USER}/)?p/({_IG_CODE})/?$")
_IG_REEL = re.compile(rf"^/(?:{_IG_USER}/)?(?:reel|reels|tv)/({_IG_CODE})/?$")
_IG_HIGHLIGHT = re.compile(r"^/stories/highlights/(\d{5,25})/?$")
_IG_SHARE = re.compile(r"^/s/([A-Za-z0-9_=-]{8,200})/?$")
_IG_STORY = re.compile(rf"^/stories/({_IG_USER})/(\d{{5,25}})/?$")

_TT_VIDEO = re.compile(rf"^/@({_TT_USER})/video/(\d{{8,25}})/?$")
_TT_PHOTO = re.compile(rf"^/@({_TT_USER})/photo/(\d{{8,25}})/?$")
_TT_SHORT = re.compile(r"^/(?:t/)?([A-Za-z0-9]{5,20})/?$")

_YT_PATH_ID = re.compile(r"^/(shorts|live|embed|v)/([A-Za-z0-9_-]{11})/?$")


@dataclass(frozen=True)
class ParsedUrl:
    platform: Platform
    kind: UrlKind
    canonical_url: str
    identifier: str


def _looks_like_url(value: str) -> bool:
    return bool(re.match(r"^(https?://)?[\w.-]+\.[a-z]{2,}(/|$)", value, re.IGNORECASE))


def _split(raw: str):
    value = raw.strip()
    if not value:
        raise AppError(ErrorCode.INVALID_URL, "Paste a link first.")
    if len(value) > MAX_URL_LENGTH:
        raise AppError(ErrorCode.INVALID_URL, "That link is too long.")
    if any(ch.isspace() for ch in value) or any(ord(ch) < 32 for ch in value):
        raise AppError(ErrorCode.INVALID_URL)
    if not re.match(r"^[a-z][a-z0-9+.-]*://", value, re.IGNORECASE):
        value = "https://" + value
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError as exc:
        raise AppError(ErrorCode.INVALID_URL) from exc
    if parts.scheme.lower() not in {"http", "https"}:
        raise AppError(ErrorCode.INVALID_URL, "Only web links (https://) are supported.")
    if parts.username or parts.password or "@" in parts.netloc:
        raise AppError(ErrorCode.INVALID_URL)
    if port not in (None, 80, 443):
        raise AppError(ErrorCode.INVALID_URL)
    host = (parts.hostname or "").rstrip(".").lower()
    if not host or not host.isascii():
        raise AppError(ErrorCode.INVALID_URL)
    return host, parts, value


def detect_platform(host: str) -> Platform | None:
    for platform, hosts in PLATFORM_HOSTS.items():
        if host in hosts:
            return platform
    return None


def _decode_share_token(token: str) -> str | None:
    padded = token + "=" * (-len(token) % 4)
    try:
        decoded = base64.urlsafe_b64decode(padded).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return None
    return decoded


def _parse_instagram(path: str) -> ParsedUrl:
    if m := _IG_POST.match(path):
        code = m.group(1)
        return ParsedUrl(Platform.INSTAGRAM, UrlKind.INSTAGRAM_POST, f"https://www.instagram.com/p/{code}/", code)
    if m := _IG_REEL.match(path):
        code = m.group(1)
        return ParsedUrl(Platform.INSTAGRAM, UrlKind.INSTAGRAM_REEL, f"https://www.instagram.com/reel/{code}/", code)
    if m := _IG_HIGHLIGHT.match(path):
        hid = m.group(1)
        return ParsedUrl(Platform.INSTAGRAM, UrlKind.INSTAGRAM_HIGHLIGHT, f"https://www.instagram.com/stories/highlights/{hid}/", hid)
    if m := _IG_SHARE.match(path):
        decoded = _decode_share_token(m.group(1)) or ""
        hm = re.fullmatch(r"highlight:(\d{5,25})", decoded)
        if hm:
            hid = hm.group(1)
            return ParsedUrl(Platform.INSTAGRAM, UrlKind.INSTAGRAM_HIGHLIGHT, f"https://www.instagram.com/stories/highlights/{hid}/", hid)
        raise AppError(ErrorCode.UNSUPPORTED_URL, "This Instagram share link isn't a highlight or post link.")
    if m := _IG_STORY.match(path):
        user, sid = m.groups()
        return ParsedUrl(Platform.INSTAGRAM, UrlKind.INSTAGRAM_STORY, f"https://www.instagram.com/stories/{user}/{sid}/", sid)
    raise AppError(ErrorCode.UNSUPPORTED_URL, "Paste a link to an Instagram post, reel or highlight (profile links aren't supported).")


def _parse_tiktok(host: str, path: str) -> ParsedUrl:
    if m := _TT_VIDEO.match(path):
        user, vid = m.groups()
        return ParsedUrl(Platform.TIKTOK, UrlKind.TIKTOK_VIDEO, f"https://www.tiktok.com/@{user}/video/{vid}", vid)
    if m := _TT_PHOTO.match(path):
        user, pid = m.groups()
        return ParsedUrl(Platform.TIKTOK, UrlKind.TIKTOK_PHOTO, f"https://www.tiktok.com/@{user}/photo/{pid}", pid)
    if host in {"vm.tiktok.com", "vt.tiktok.com"} and (m := _TT_SHORT.match(path)):
        code = m.group(1)
        return ParsedUrl(Platform.TIKTOK, UrlKind.TIKTOK_SHORT_LINK, f"https://{host}/{code}/", code)
    if path.startswith("/t/") and (m := _TT_SHORT.match(path)):
        code = m.group(1)
        return ParsedUrl(Platform.TIKTOK, UrlKind.TIKTOK_SHORT_LINK, f"https://www.tiktok.com/t/{code}/", code)
    raise AppError(ErrorCode.UNSUPPORTED_URL, "Paste a link to a TikTok video or photo post (profile links aren't supported).")


def _parse_youtube(host: str, path: str, query: str) -> ParsedUrl:
    if host == "youtu.be":
        vid = path.strip("/")
        if _YT_ID.match(vid):
            return ParsedUrl(Platform.YOUTUBE, UrlKind.YOUTUBE_VIDEO, f"https://www.youtube.com/watch?v={vid}", vid)
        raise AppError(ErrorCode.UNSUPPORTED_URL)
    if path.rstrip("/") == "/watch":
        vid = (parse_qs(query).get("v") or [""])[0]
        if _YT_ID.match(vid):
            return ParsedUrl(Platform.YOUTUBE, UrlKind.YOUTUBE_VIDEO, f"https://www.youtube.com/watch?v={vid}", vid)
        raise AppError(ErrorCode.INVALID_URL, "This YouTube link is missing a valid video ID.")
    if m := _YT_PATH_ID.match(path):
        section, vid = m.groups()
        if section == "shorts":
            return ParsedUrl(Platform.YOUTUBE, UrlKind.YOUTUBE_SHORT, f"https://www.youtube.com/shorts/{vid}", vid)
        return ParsedUrl(Platform.YOUTUBE, UrlKind.YOUTUBE_VIDEO, f"https://www.youtube.com/watch?v={vid}", vid)
    if path.rstrip("/") == "/playlist":
        raise AppError(ErrorCode.UNSUPPORTED_CONTENT_TYPE, "Playlists aren't supported. Paste a single video or Short link.")
    raise AppError(ErrorCode.UNSUPPORTED_URL, "Paste a link to a single YouTube video or Short.")


def parse_supported_url(raw: str, expected: Platform | None = None) -> ParsedUrl:
    """Validate ``raw`` and return a canonical, allowlisted URL.

    Raises ``AppError`` with a precise code for every rejection.
    """
    host, parts, value = _split(raw)
    platform = detect_platform(host)
    if platform is None:
        if _looks_like_url(value):
            raise AppError(ErrorCode.UNSUPPORTED_PLATFORM)
        raise AppError(ErrorCode.INVALID_URL)
    if expected is not None and platform != expected:
        raise AppError(
            ErrorCode.UNSUPPORTED_PLATFORM,
            f"This is a {PLATFORM_NAMES[platform.value]} link. Use the {PLATFORM_NAMES[platform.value]} page for it.",
        )
    path = parts.path or "/"
    if platform is Platform.INSTAGRAM:
        return _parse_instagram(path)
    if platform is Platform.TIKTOK:
        return _parse_tiktok(host, path)
    return _parse_youtube(host, path, parts.query)
