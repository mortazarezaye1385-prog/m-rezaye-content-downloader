"""Public API schemas. These are the only shapes the browser ever sees."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator

from app.security.url_validation import MAX_URL_LENGTH, Platform

MAX_TICKET_LENGTH = 48 * 1024


class MediaKind(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


class SourceCondition(str, Enum):
    """What the provider actually reports about watermarks. Never inferred."""

    WATERMARK_FREE = "watermark_free"
    WATERMARKED = "watermarked"
    UNKNOWN = "unknown"


class ContentType(str, Enum):
    PHOTO = "photo"
    VIDEO = "video"
    CAROUSEL = "carousel"
    HIGHLIGHT = "highlight"
    SHORT = "short"


class Orientation(str, Enum):
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"
    SQUARE = "square"


class Dimensions(BaseModel):
    width: int
    height: int


class QualityOption(BaseModel):
    id: str
    label: str
    tier: str | None = None
    height: int
    width: int | None = None
    fps: float | None = None
    hdr: bool = False
    container: str
    video_codec: str | None = None
    audio_codec: str | None = None
    approx_bytes: int | None = None
    requires_merge: bool = False


class MediaItem(BaseModel):
    index: int
    kind: MediaKind
    preview_url: str | None = None
    dimensions: Dimensions | None = None
    duration_seconds: float | None = None
    format: str | None = None
    approx_bytes: int | None = None
    source_condition: SourceCondition = SourceCondition.UNKNOWN
    quality_note: str = "Highest available quality"
    ticket: str


class MediaAnalysis(BaseModel):
    platform: Platform
    content_type: ContentType
    title: str | None = None
    author: str | None = None
    items: list[MediaItem]
    bundle_ticket: str | None = None
    orientation: Orientation | None = None
    aspect_ratio: str | None = None
    duration_seconds: float | None = None
    qualities: list[QualityOption] | None = None
    retrieval: str
    notices: list[str] = Field(default_factory=list)


class CaptionResult(BaseModel):
    platform: Platform
    caption: str | None
    author: str | None = None
    retrieval: str


class UrlRequest(BaseModel):
    url: str = Field(min_length=1, max_length=MAX_URL_LENGTH)

    @field_validator("url")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()


class DownloadRequest(BaseModel):
    ticket: str = Field(min_length=10, max_length=MAX_TICKET_LENGTH)
    quality_id: str | None = Field(default=None, max_length=40, pattern=r"^[A-Za-z0-9_-]+$")
