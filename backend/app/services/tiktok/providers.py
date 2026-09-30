"""TikTok providers: official oEmbed (captions/metadata) + public extractor (media)."""

from __future__ import annotations

from typing import Any

from app.core.config import Settings
from app.core.errors import AppError, ErrorCode
from app.security.url_validation import ParsedUrl, UrlKind
from app.services.base import NormalizedMedia, ProviderSkip, run_blocking
from app.services.engine_normalize import TIKTOK_SELECTOR, normalize_engine_info, tiktok_source_condition
from app.services.ytdlp_client import YtDlpClient
from app.utils.http import get_json

OEMBED_URL = "https://www.tiktok.com/oembed"


class TikTokOEmbedProvider:
    """TikTok's official, public oEmbed endpoint. Captions only; no media files."""

    name = "TikTok oEmbed (official)"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def caption(self, parsed: ParsedUrl) -> tuple[str | None, str | None]:
        if parsed.kind is UrlKind.TIKTOK_SHORT_LINK:
            raise ProviderSkip()
        status, body = await get_json(OEMBED_URL, params={"url": parsed.canonical_url}, timeout=self.settings.network_timeout_seconds)
        if status != 200 or not isinstance(body, dict):
            raise ProviderSkip()
        return (body.get("title") or None), body.get("author_name")

    async def fetch(self, parsed: ParsedUrl) -> NormalizedMedia:
        raise ProviderSkip()  # oEmbed exposes no media files


class TikTokEngineProvider:
    name = "Public TikTok extractor (logged out)"

    def __init__(self, settings: Settings, engine: YtDlpClient) -> None:
        self.settings = settings
        self.engine = engine

    async def info(self, parsed: ParsedUrl) -> dict[str, Any]:
        return await run_blocking(
            lambda: self.engine.extract(parsed.canonical_url, platform="tiktok", allow_playlist=True),
            self.settings.extraction_timeout_seconds,
        )

    async def fetch(self, parsed: ParsedUrl) -> NormalizedMedia:
        info = await self.info(parsed)
        media = normalize_engine_info(info, provider=self.name, selector=TIKTOK_SELECTOR, condition=tiktok_source_condition)
        if not media.items:
            raise AppError(
                ErrorCode.UNSUPPORTED_BY_PROVIDER,
                "TikTok photo posts aren't exposed as downloadable images by the current retrieval method. Video posts work.",
            )
        return media

    async def caption(self, parsed: ParsedUrl) -> tuple[str | None, str | None]:
        info = await self.info(parsed)
        return (info.get("description") or info.get("title") or None), info.get("uploader")
