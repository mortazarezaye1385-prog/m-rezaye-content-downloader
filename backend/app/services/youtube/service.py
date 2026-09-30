from __future__ import annotations

from typing import Any

from app.core.errors import AppError, ErrorCode
from app.schemas.media import CaptionResult, ContentType, MediaAnalysis, MediaKind, Orientation
from app.security.url_validation import ParsedUrl, Platform, UrlKind
from app.services.base import DownloadPlan, NormalizedItem, NormalizedMedia, PlanStep, PlatformService, run_blocking
from app.services.media_utils import aspect_label, best_thumbnail, best_video_dimensions, orientation_of
from app.services.youtube.quality import build_quality_options, resolve_quality
from app.services.ytdlp_client import YtDlpClient

SHORT_MAX_SECONDS = 180


def classify(kind: UrlKind, orientation: Orientation | None, duration: float | None) -> ContentType:
    """A Short is a /shorts/ link, or a vertical video within the Shorts length limit."""
    if kind is UrlKind.YOUTUBE_SHORT:
        return ContentType.SHORT
    if orientation is Orientation.VERTICAL and duration is not None and duration <= SHORT_MAX_SECONDS:
        return ContentType.SHORT
    return ContentType.VIDEO


class YouTubeService(PlatformService):
    platform = Platform.YOUTUBE

    def __init__(self, settings, signer, engine: YtDlpClient | None = None) -> None:
        super().__init__(settings, signer)
        self.engine = engine or YtDlpClient(settings)

    async def _info(self, url: str) -> dict[str, Any]:
        info = await run_blocking(lambda: self.engine.extract(url, platform="youtube"), self.settings.extraction_timeout_seconds)
        if info.get("is_live") or info.get("live_status") in {"is_live", "is_upcoming"}:
            raise AppError(ErrorCode.UNSUPPORTED_CONTENT_TYPE, "Live streams and premieres that haven't finished can't be downloaded.")
        return info

    async def analyze(self, parsed: ParsedUrl) -> MediaAnalysis:
        info = await self._info(parsed.canonical_url)
        formats = info.get("formats") or []
        qualities = build_quality_options(formats)
        if not qualities:
            if any(f.get("has_drm") for f in formats):
                raise AppError(ErrorCode.DRM_PROTECTED)
            raise AppError(ErrorCode.UNSUPPORTED_BY_PROVIDER, "No downloadable video formats were offered for this video.")
        width, height = best_video_dimensions(info)
        orientation = orientation_of(width, height)
        duration = info.get("duration")
        content_type = classify(parsed.kind, orientation, duration)
        media = NormalizedMedia(
            provider=self.engine.name,
            title=info.get("title"),
            author=info.get("channel") or info.get("uploader"),
            caption=info.get("description"),
            items=[NormalizedItem(kind=MediaKind.VIDEO, preview_src=best_thumbnail(info), width=width, height=height, duration=duration, ext=qualities[0].container)],
        )
        items = self.to_items(parsed, media, content_type)
        return MediaAnalysis(
            platform=self.platform,
            content_type=content_type,
            title=media.title,
            author=media.author,
            items=items,
            orientation=orientation,
            aspect_ratio=aspect_label(width, height),
            duration_seconds=duration,
            qualities=qualities,
            retrieval=self.engine.name,
            notices=["Qualities listed are exactly what YouTube offers for this video right now."],
        )

    async def caption(self, parsed: ParsedUrl) -> CaptionResult:
        info = await self._info(parsed.canonical_url)
        return CaptionResult(platform=self.platform, caption=(info.get("description") or None), author=info.get("channel"), retrieval=self.engine.name)

    async def plan_download(self, ticket: dict[str, Any], quality_id: str | None) -> DownloadPlan:
        if not quality_id:
            raise AppError(ErrorCode.VALIDATION_ERROR, "Select a quality first.")
        # Re-read formats now: URLs expire and availability can change.
        info = await self._info(ticket["u"])
        chosen = resolve_quality(info.get("formats") or [], quality_id)
        step = PlanStep(
            method="engine",
            source_url=ticket["u"],
            ext=chosen.option.container,
            format_selector=chosen.format_selector,
            merge_format=chosen.merge_format,
            expected_bytes=chosen.option.approx_bytes,
        )
        title = ticket.get("t") or info.get("title")
        return DownloadPlan(self.platform, f"{title} {chosen.option.label}", [step])
