from __future__ import annotations

from typing import Any

from app.schemas.media import CaptionResult, ContentType, MediaAnalysis, MediaKind
from app.security.url_validation import ParsedUrl, Platform
from app.services.base import DownloadPlan, NormalizedMedia, PlatformService
from app.services.media_utils import aspect_label, orientation_of
from app.services.tiktok.providers import TikTokEngineProvider, TikTokOEmbedProvider
from app.services.ytdlp_client import YtDlpClient


def tiktok_content_type(media: NormalizedMedia) -> ContentType:
    if len(media.items) > 1:
        return ContentType.CAROUSEL
    return ContentType.PHOTO if media.items[0].kind is MediaKind.IMAGE else ContentType.VIDEO


class TikTokService(PlatformService):
    platform = Platform.TIKTOK

    def __init__(self, settings, signer, engine: YtDlpClient | None = None, media_providers: list[Any] | None = None, caption_providers: list[Any] | None = None) -> None:
        super().__init__(settings, signer)
        engine_provider = TikTokEngineProvider(settings, engine or YtDlpClient(settings))
        self.media_providers = media_providers or [engine_provider]
        self.caption_providers = caption_providers or [TikTokOEmbedProvider(settings), engine_provider]

    async def analyze(self, parsed: ParsedUrl) -> MediaAnalysis:
        media: NormalizedMedia = await self.first_success(self.media_providers, lambda p: p.fetch(parsed))
        content_type = tiktok_content_type(media)
        items = self.to_items(parsed, media, content_type)
        bundle = self.bundle_ticket(parsed, media, content_type)
        first = media.items[0]
        return MediaAnalysis(
            platform=self.platform,
            content_type=content_type,
            title=media.title,
            author=media.author,
            items=items,
            bundle_ticket=bundle,
            orientation=orientation_of(first.width, first.height),
            aspect_ratio=aspect_label(first.width, first.height),
            duration_seconds=first.duration,
            retrieval=media.provider,
            notices=media.notices + ["When TikTok itself offers a rendition without a watermark it is preferred. Watermarks are never removed or altered."],
        )

    async def caption(self, parsed: ParsedUrl) -> CaptionResult:
        async def call(provider):
            text, author = await provider.caption(parsed)
            return CaptionResult(platform=self.platform, caption=(text or None), author=author, retrieval=provider.name)

        return await self.first_success(self.caption_providers, call)

    async def plan_download(self, ticket: dict[str, Any], quality_id: str | None) -> DownloadPlan:
        return self.plan_from_tickets(ticket)
