"""Convert retrieval-engine metadata into NormalizedMedia, honestly."""

from __future__ import annotations

from typing import Any, Callable

from app.schemas.media import MediaKind, SourceCondition
from app.services.base import NormalizedItem, NormalizedMedia
from app.services.media_utils import best_thumbnail, format_bytes, is_drm, is_video_format

WATERMARK_TAG = "watermark"

# Prefer non-watermarked renditions *when the source itself offers one*.
TIKTOK_SELECTOR = "b[format_note!*=watermark]/bv*[format_note!*=watermark]+ba/b"
GENERIC_SELECTOR = "bv*+ba/b"


def tiktok_source_condition(formats: list[dict[str, Any]]) -> SourceCondition:
    video = [f for f in formats if is_video_format(f)]
    if video and all(WATERMARK_TAG in (f.get("format_note") or "").lower() for f in video):
        return SourceCondition.WATERMARKED
    # Engine never positively certifies "no watermark", so we don't either.
    return SourceCondition.UNKNOWN


def _item_from_entry(entry: dict[str, Any], playlist_index: int | None, selector: str, condition: Callable[[list[dict[str, Any]]], SourceCondition]) -> NormalizedItem | None:
    formats = [f for f in entry.get("formats") or [] if not is_drm(f)]
    video = [f for f in formats if is_video_format(f)]
    if not video:
        return None
    best = max(video, key=lambda f: (f.get("height") or 0, f.get("tbr") or 0))
    return NormalizedItem(
        kind=MediaKind.VIDEO,
        preview_src=best_thumbnail(entry),
        width=best.get("width"),
        height=best.get("height"),
        duration=entry.get("duration"),
        ext=entry.get("ext") or best.get("ext") or "mp4",
        approx_bytes=format_bytes(best),
        source_condition=condition(formats),
        playlist_index=playlist_index,
        format_selector=selector,
    )


def normalize_engine_info(
    info: dict[str, Any],
    *,
    provider: str,
    selector: str = GENERIC_SELECTOR,
    condition: Callable[[list[dict[str, Any]]], SourceCondition] = lambda _f: SourceCondition.UNKNOWN,
) -> NormalizedMedia:
    entries = info.get("entries") if info.get("_type") == "playlist" else None
    items: list[NormalizedItem] = []
    skipped = 0
    if entries:
        for idx, entry in enumerate(entries, start=1):
            if not entry:
                skipped += 1
                continue
            item = _item_from_entry(entry, idx, selector, condition)
            if item is None:
                skipped += 1
            else:
                items.append(item)
    else:
        item = _item_from_entry(info, None, selector, condition)
        if item:
            items.append(item)
    first = (entries[0] if entries and entries[0] else info) or {}
    notices = []
    if skipped:
        notices.append(f"{skipped} item(s) weren't exposed as downloadable media by the retrieval method.")
    return NormalizedMedia(
        provider=provider,
        title=info.get("title") or first.get("title"),
        author=info.get("uploader") or first.get("uploader") or info.get("channel"),
        caption=info.get("description") or first.get("description"),
        items=items,
        raw_info=info,
        notices=notices,
    )
