"""Instagram retrieval providers, tried in order.

1. InstagramGraphProvider: the official Instagram API, only for media owned by
   the account whose token you configured. Fully authorized, but it can't see
   other accounts' posts and exposes no Highlights endpoint.
2. InstagramEngineProvider: public, logged-out extraction. Never authenticates.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

from app.core.config import Settings
from app.core.errors import AppError, ErrorCode
from app.schemas.media import MediaKind
from app.security.url_validation import ParsedUrl, UrlKind
from app.services.base import NormalizedItem, NormalizedMedia, ProviderSkip, run_blocking
from app.services.engine_normalize import normalize_engine_info
from app.services.ytdlp_client import YtDlpClient
from app.utils.http import get_json

GRAPH_FIELDS = "id,caption,media_type,media_url,thumbnail_url,permalink,username,children{media_type,media_url,thumbnail_url}"


def _ext_from_url(url: str | None, fallback: str) -> str:
    path = urlsplit(url or "").path.lower()
    for ext in ("jpg", "jpeg", "png", "webp", "heic", "mp4", "mov"):
        if path.endswith("." + ext):
            return "jpg" if ext == "jpeg" else ext
    return fallback


def graph_node_to_item(node: dict[str, Any]) -> NormalizedItem | None:
    media_type = node.get("media_type")
    media_url = node.get("media_url")
    if not media_url:
        return None  # e.g. copyrighted audio reels omit media_url
    if media_type == "VIDEO":
        return NormalizedItem(kind=MediaKind.VIDEO, preview_src=node.get("thumbnail_url"), ext=_ext_from_url(media_url, "mp4"), direct_url=media_url)
    if media_type == "IMAGE":
        return NormalizedItem(kind=MediaKind.IMAGE, preview_src=media_url, ext=_ext_from_url(media_url, "jpg"), direct_url=media_url)
    return None


def shortcode_matches(permalink: str | None, shortcode: str) -> bool:
    segments = [s for s in urlsplit(permalink or "").path.split("/") if s]
    return shortcode in segments


class InstagramGraphProvider:
    name = "Instagram API (your own account)"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def enabled_for(self, parsed: ParsedUrl) -> bool:
        return self.settings.instagram_graph_enabled and parsed.kind in {UrlKind.INSTAGRAM_POST, UrlKind.INSTAGRAM_REEL}

    async def fetch(self, parsed: ParsedUrl) -> NormalizedMedia:
        if not self.enabled_for(parsed):
            raise ProviderSkip()
        s = self.settings
        url: str | None = f"https://graph.instagram.com/{s.instagram_graph_api_version}/{s.instagram_graph_user_id}/media"
        params: dict[str, Any] | None = {"fields": GRAPH_FIELDS, "limit": 50, "access_token": s.instagram_graph_access_token}
        for _ in range(s.instagram_graph_max_pages):
            if not url:
                break
            status, body = await get_json(url, params=params, timeout=s.network_timeout_seconds)
            if status != 200 or not isinstance(body, dict):
                err = (body or {}).get("error", {}) if isinstance(body, dict) else {}
                if err.get("code") in (4, 17, 32, 613):
                    raise AppError(ErrorCode.UPSTREAM_RATE_LIMITED)
                raise ProviderSkip()  # token/permissions issue: fall back quietly
            for node in body.get("data", []):
                if shortcode_matches(node.get("permalink"), parsed.identifier):
                    return self._to_media(node)
            url = (body.get("paging") or {}).get("next")
            params = None  # "next" already carries the query
        raise ProviderSkip()  # not media owned by the configured account

    def _to_media(self, node: dict[str, Any]) -> NormalizedMedia:
        nodes = (node.get("children") or {}).get("data") if node.get("media_type") == "CAROUSEL_ALBUM" else [node]
        items = [item for item in (graph_node_to_item(n) for n in nodes or []) if item]
        notices = [] if len(items) == len(nodes or []) else ["Some items weren't provided by the Instagram API (for example reels with licensed audio)."]
        return NormalizedMedia(provider=self.name, title=None, author=node.get("username"), caption=node.get("caption"), items=items, notices=notices)

    async def caption(self, parsed: ParsedUrl) -> tuple[str | None, str | None]:
        media = await self.fetch(parsed)
        return media.caption, media.author


class InstagramEngineProvider:
    name = "Public Instagram extractor (logged out)"

    def __init__(self, settings: Settings, engine: YtDlpClient) -> None:
        self.settings = settings
        self.engine = engine

    async def info(self, parsed: ParsedUrl) -> dict[str, Any]:
        allow_playlist = parsed.kind in {UrlKind.INSTAGRAM_POST, UrlKind.INSTAGRAM_HIGHLIGHT}
        return await run_blocking(
            lambda: self.engine.extract(parsed.canonical_url, platform="instagram", allow_playlist=allow_playlist),
            self.settings.extraction_timeout_seconds,
        )

    async def fetch(self, parsed: ParsedUrl) -> NormalizedMedia:
        info = await self.info(parsed)
        media = normalize_engine_info(info, provider=self.name)
        if not media.items:
            raise AppError(
                ErrorCode.UNSUPPORTED_BY_PROVIDER,
                "The public extractor only exposes Instagram videos. Photo posts can be retrieved through the official Instagram API for posts on your own account (see README).",
            )
        return media

    async def caption(self, parsed: ParsedUrl) -> tuple[str | None, str | None]:
        info = await self.info(parsed)
        media = normalize_engine_info(info, provider=self.name)
        return media.caption, media.author
