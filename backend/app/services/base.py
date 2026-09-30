"""Platform service abstraction and the provider-chain contract.

Frontend <-> API <-> PlatformService <-> RetrievalProvider(s) <-> processors.

A PlatformService owns one platform. It asks its providers in order; a provider
that can't handle a request raises ``ProviderSkip`` so the next one is tried.
Adding a newly permitted retrieval mechanism means adding a provider, not
touching the frontend.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence, TypeVar

from app.core.config import Settings
from app.core.errors import AppError, ErrorCode
from app.schemas.media import (
    CaptionResult,
    ContentType,
    Dimensions,
    MediaAnalysis,
    MediaItem,
    MediaKind,
    SourceCondition,
)
from app.security.tickets import TicketSigner
from app.security.url_validation import ParsedUrl, Platform

T = TypeVar("T")

TICKET_DOWNLOAD = "download"
TICKET_PREVIEW = "preview"


class ProviderSkip(Exception):
    """Raised by a provider that doesn't cover this request."""


@dataclass
class NormalizedItem:
    kind: MediaKind
    preview_src: str | None = None
    width: int | None = None
    height: int | None = None
    duration: float | None = None
    ext: str | None = None
    approx_bytes: int | None = None
    source_condition: SourceCondition = SourceCondition.UNKNOWN
    direct_url: str | None = None
    playlist_index: int | None = None
    format_selector: str | None = None


@dataclass
class NormalizedMedia:
    provider: str
    title: str | None
    author: str | None
    caption: str | None
    items: list[NormalizedItem]
    raw_info: dict[str, Any] | None = None
    notices: list[str] = field(default_factory=list)


@dataclass
class PlanStep:
    method: str  # "engine" | "direct"
    source_url: str
    ext: str | None
    format_selector: str | None = None
    playlist_index: int | None = None
    merge_format: str | None = None
    direct_url: str | None = None
    expected_bytes: int | None = None


@dataclass
class DownloadPlan:
    platform: Platform
    title: str | None
    steps: list[PlanStep]
    bundle: bool = False


async def run_blocking(func: Callable[[], T], timeout: float) -> T:
    try:
        return await asyncio.wait_for(asyncio.to_thread(func), timeout=timeout)
    except asyncio.TimeoutError as exc:
        raise AppError(ErrorCode.UPSTREAM_TIMEOUT) from exc


class PlatformService(ABC):
    platform: Platform

    def __init__(self, settings: Settings, signer: TicketSigner) -> None:
        self.settings = settings
        self.signer = signer

    # ---- contract -------------------------------------------------------
    @abstractmethod
    async def analyze(self, parsed: ParsedUrl) -> MediaAnalysis: ...

    @abstractmethod
    async def caption(self, parsed: ParsedUrl) -> CaptionResult: ...

    @abstractmethod
    async def plan_download(self, ticket: dict[str, Any], quality_id: str | None) -> DownloadPlan: ...

    # ---- shared helpers -------------------------------------------------
    async def first_success(self, providers: Sequence[Any], call: Callable[[Any], Any]) -> Any:
        last_error: AppError | None = None
        for provider in providers:
            try:
                return await call(provider)
            except ProviderSkip:
                continue
            except AppError as err:
                # Hard access answers are final; don't shop around for a way in.
                if err.code in {ErrorCode.PRIVATE_CONTENT, ErrorCode.CONTENT_DELETED, ErrorCode.DRM_PROTECTED}:
                    raise
                last_error = err
        if last_error:
            raise last_error
        raise AppError(ErrorCode.UNSUPPORTED_BY_PROVIDER)

    def preview_token(self, src: str | None) -> str | None:
        if not src:
            return None
        token = self.signer.sign({"u": src}, purpose=TICKET_PREVIEW, ttl_seconds=self.settings.ticket_ttl_seconds)
        return f"/api/preview?t={token}"

    def item_payload(self, parsed: ParsedUrl, media: NormalizedMedia, index: int, item: NormalizedItem, content_type: ContentType) -> dict[str, Any]:
        return {
            "p": self.platform.value,
            "u": parsed.canonical_url,
            "k": "item",
            "ct": content_type.value,
            "t": (media.title or "")[:80],
            "i": index,
            "m": item.kind.value,
            "x": item.ext,
            "pl": item.playlist_index,
            "fs": item.format_selector,
            "d": item.direct_url,
            "b": item.approx_bytes,
        }

    def item_ticket(self, parsed: ParsedUrl, media: NormalizedMedia, index: int, item: NormalizedItem, content_type: ContentType) -> str:
        payload = self.item_payload(parsed, media, index, item, content_type)
        return self.signer.sign(payload, purpose=TICKET_DOWNLOAD, ttl_seconds=self.settings.ticket_ttl_seconds)

    def bundle_ticket(self, parsed: ParsedUrl, media: NormalizedMedia, content_type: ContentType) -> str | None:
        """One signed ticket covering every item (for Download All)."""
        if len(media.items) < 2:
            return None
        payloads = [self.item_payload(parsed, media, i, item, content_type) for i, item in enumerate(media.items)]
        payload = {"p": self.platform.value, "u": parsed.canonical_url, "k": "bundle", "ct": content_type.value, "t": (media.title or "")[:80], "items": payloads}
        return self.signer.sign(payload, purpose=TICKET_DOWNLOAD, ttl_seconds=self.settings.ticket_ttl_seconds)

    def to_items(self, parsed: ParsedUrl, media: NormalizedMedia, content_type: ContentType) -> list[MediaItem]:
        items: list[MediaItem] = []
        for index, item in enumerate(media.items):
            items.append(
                MediaItem(
                    index=index,
                    kind=item.kind,
                    preview_url=self.preview_token(item.preview_src),
                    dimensions=Dimensions(width=item.width, height=item.height) if item.width and item.height else None,
                    duration_seconds=item.duration,
                    format=item.ext,
                    approx_bytes=item.approx_bytes,
                    source_condition=item.source_condition,
                    ticket=self.item_ticket(parsed, media, index, item, content_type),
                )
            )
        return items

    def step_from_item_ticket(self, ticket: dict[str, Any]) -> PlanStep:
        if ticket.get("d"):
            return PlanStep(method="direct", source_url=ticket["u"], ext=ticket.get("x"), direct_url=ticket["d"], expected_bytes=ticket.get("b"))
        return PlanStep(
            method="engine",
            source_url=ticket["u"],
            ext=ticket.get("x"),
            format_selector=ticket.get("fs") or "best",
            playlist_index=ticket.get("pl"),
            expected_bytes=ticket.get("b"),
        )

    def plan_from_tickets(self, ticket: dict[str, Any]) -> DownloadPlan:
        """Default plan builder for item/bundle tickets (Instagram, TikTok)."""
        if ticket.get("k") == "bundle":
            steps = []
            for payload in ticket.get("items") or []:
                if isinstance(payload, dict) and payload.get("u") == ticket.get("u"):
                    steps.append(self.step_from_item_ticket(payload))
            if not steps:
                raise AppError(ErrorCode.INVALID_TICKET)
            return DownloadPlan(self.platform, ticket.get("t"), steps[: self.settings.max_bundle_items], bundle=True)
        return DownloadPlan(self.platform, ticket.get("t"), [self.step_from_item_ticket(ticket)])
