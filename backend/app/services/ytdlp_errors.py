"""Translate retrieval-engine error text into precise, honest error codes."""

from __future__ import annotations

import re

from app.core.errors import AppError, ErrorCode

_RULES: list[tuple[re.Pattern[str], ErrorCode]] = [
    (re.compile(r"drm|protected content", re.I), ErrorCode.DRM_PROTECTED),
    (re.compile(r"account is private|private video|private account|is private", re.I), ErrorCode.PRIVATE_CONTENT),
    (re.compile(r"confirm you.?re not a bot|captcha|bot check", re.I), ErrorCode.UPSTREAM_BLOCKED),
    (re.compile(r"sign in to confirm your age|age[- ]restricted|inappropriate for some users", re.I), ErrorCode.LOGIN_REQUIRED),
    (re.compile(r"login required|log in|requires authentication|use --cookies|cookies|members[- ]only|join this channel", re.I), ErrorCode.LOGIN_REQUIRED),
    (re.compile(r"http error 429|too many requests|rate[- ]?limit", re.I), ErrorCode.UPSTREAM_RATE_LIMITED),
    (re.compile(r"removed|deleted|terminated|no longer available|violat", re.I), ErrorCode.CONTENT_DELETED),
    (re.compile(r"not available in your country|geo|blocked it in your", re.I), ErrorCode.CONTENT_UNAVAILABLE),
    (re.compile(r"there is no video in this post|no video formats|no media found", re.I), ErrorCode.UNSUPPORTED_BY_PROVIDER),
    (re.compile(r"unsupported url", re.I), ErrorCode.UNSUPPORTED_URL),
    (re.compile(r"requested format is not available", re.I), ErrorCode.QUALITY_UNAVAILABLE),
    (re.compile(r"larger than max-filesize|max[-_ ]filesize|file is larger", re.I), ErrorCode.MEDIA_TOO_LARGE),
    (re.compile(r"timed out|timeout", re.I), ErrorCode.UPSTREAM_TIMEOUT),
    (re.compile(r"video unavailable|unavailable|http error 404|not found", re.I), ErrorCode.CONTENT_UNAVAILABLE),
    (re.compile(r"unable to download|connection|network|name resolution|ssl|reset by peer|http error 5\d\d", re.I), ErrorCode.NETWORK_ERROR),
    (re.compile(r"no space left|disk quota", re.I), ErrorCode.STORAGE_ERROR),
    (re.compile(r"ffmpeg|postprocess|merg", re.I), ErrorCode.PROCESSING_ERROR),
]

# Instagram's "rate-limit reached or login required" is a login wall in practice.
_IG_LOGIN_WALL = re.compile(r"rate-limit reached or login required|not available.*login", re.I)


def map_retrieval_error(message: str, *, platform: str | None = None) -> AppError:
    text = message or ""
    if platform == "instagram" and _IG_LOGIN_WALL.search(text):
        return AppError(ErrorCode.LOGIN_REQUIRED, internal_detail=text[:500])
    for pattern, code in _RULES:
        if pattern.search(text):
            return AppError(code, internal_detail=text[:500])
    return AppError(ErrorCode.RETRIEVAL_FAILED, internal_detail=text[:500])
