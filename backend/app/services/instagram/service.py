from __future__ import annotations

from typing import Any

from app.core.errors import AppError, ErrorCode
from app.schemas.media import CaptionResult, ContentType, MediaAnalysis, MediaKind
from app.security.url_validation import ParsedUrl, Platform, UrlKind
from app.services.base import DownloadPlan, NormalizedMedia, PlatformService
from app.services.instagram.providers import InstagramEngineProvider, InstagramGraphProvider
from app.services.media_utils import aspect_label, orientation_of
from app.services.ytdlp_client import YtDlpClient

HIGHLIGHT_LOGIN_WALL = (
    "Instagram only serves Highlights to signed-in viewers. This app never signs in or uses "
    "session cookies, so the current retrieval method can't access this Highlight. Nothing was bypassed."
)


def content_type_for(parsed: ParsedUrl, media: NormalizedMedia) -> ContentType:
    if parsed.kind is UrlKind.INSTAGRAM_HIGHLIGHT:
        return ContentType.HIGHLIGHT
    if len(media.items) > 1:
        return ContentType.CAROUSEL
    return ContentType.PHOTO if media.items and media.items[0].kind is MediaKind.IMAGE else ContentType.VIDEO


class InstagramService(PlatformService):
    platform = Platform.INSTAGRAM

    def __init__(self, settings, signer, engine: YtDlpClient | None = None, providers: list[Any] | None = None) -> None:
        super().__init__(settings, signer)
        engine = engine or YtDlpClient(settings)
        self.providers = providers or [InstagramGraphProvider(settings), InstagramEngineProvider(settings, engine)]

    def _require_media_url(self, parsed: ParsedUrl) -> None:
        if parsed.kind is UrlKind.INSTAGRAM_STORY:
            raise AppError(ErrorCode.UNSUPPORTED_CONTENT_TYPE, "Individual stories aren't supported. Paste a post, reel or Highlight link.")
        if parsed.kind is UrlKind.INSTAGRAM_HIGHLIGHT:
            raise AppError(ErrorCode.UNSUPPORTED_URL, "That's a Highlight link. Use the Highlights section below.")

    async def _fetch(self, parsed: ParsedUrl) -> NormalizedMedia:
        return await self.first_success(self.providers, lambda p: p.fetch(parsed))

    def _build(self, parsed: ParsedUrl, media: NormalizedMedia) -> MediaAnalysis:
        content_type = content_type_for(parsed, media)
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
            orientation=orientation_of(first.width, first.height) if len(items) == 1 else None,
            aspect_ratio=aspect_label(first.width, first.height) if len(items) == 1 else None,
            duration_seconds=first.duration if len(items) == 1 else None,
            retrieval=media.provider,
            notices=media.notices,
        )

    async def analyze(self, parsed: ParsedUrl) -> MediaAnalysis:
        self._require_media_url(parsed)
        return self._build(parsed, await self._fetch(parsed))

    async def analyze_highlight(self, parsed: ParsedUrl) -> MediaAnalysis:
        if parsed.kind is not UrlKind.INSTAGRAM_HIGHLIGHT:
            raise AppError(ErrorCode.INVALID_URL, "That isn't a Highlight link. Highlight links look like instagram.com/stories/highlights/…")
        try:
            media = await self._fetch(parsed)
        except AppError as err:
            if err.code is ErrorCode.LOGIN_REQUIRED:
                raise AppError(ErrorCode.UNSUPPORTED_BY_PROVIDER, HIGHLIGHT_LOGIN_WALL, internal_detail=err.internal_detail) from err
            raise
        return self._build(parsed, media)

    async def caption(self, parsed: ParsedUrl) -> CaptionResult:
        self._require_media_url(parsed)

        async def call(provider):
            text, author = await provider.caption(parsed)
            return CaptionResult(platform=self.platform, caption=(text or None), author=author, retrieval=provider.name)

        return await self.first_success(self.providers, call)

    async def plan_download(self, ticket: dict[str, Any], quality_id: str | None) -> DownloadPlan:
        return self.plan_from_tickets(ticket)
