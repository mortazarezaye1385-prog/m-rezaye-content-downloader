"""Build the list of qualities YouTube *actually* offers for one video.

Nothing here invents a resolution: every option maps to real format ids
reported by the retrieval engine. Resolution is re-checked at download time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.errors import AppError, ErrorCode
from app.schemas.media import QualityOption
from app.services.media_utils import format_bytes, is_audio_only, is_drm, is_video_format

TIERS: dict[int, str] = {4320: "8K", 2160: "4K", 1440: "2K", 1080: "Full HD", 720: "HD"}
_CODEC_RANK = {"avc1": 0, "h264": 0, "vp09": 1, "vp9": 1, "av01": 2, "hev1": 3, "hvc1": 3}


def _codec_family(codec: str | None) -> str:
    return (codec or "").split(".")[0].lower()


def _fps_bucket(fps: float | None) -> int | None:
    if not fps:
        return None
    return int(round(fps))


def quality_id(height: int, fps: float | None, hdr: bool) -> str:
    bucket = _fps_bucket(fps)
    ident = f"{height}p"
    if bucket and bucket > 30:
        ident += str(bucket)
    if hdr:
        ident += "-hdr"
    return ident


@dataclass(frozen=True)
class ResolvedQuality:
    option: QualityOption
    format_selector: str
    merge_format: str | None


def _pick_audio(audios: list[dict[str, Any]], video_ext: str) -> dict[str, Any] | None:
    if not audios:
        return None
    preferred = "m4a" if video_ext == "mp4" else "webm"
    same = [a for a in audios if a.get("ext") == preferred]
    pool = same or audios
    return max(pool, key=lambda a: (a.get("abr") or a.get("tbr") or 0))


def _container(video_ext: str, audio_ext: str | None) -> str:
    if audio_ext is None:
        return video_ext
    if video_ext == "mp4" and audio_ext in {"m4a", "mp4"}:
        return "mp4"
    if video_ext == "webm" and audio_ext == "webm":
        return "webm"
    return "mkv"  # stream-copy container that accepts any codec pair


def resolve_all(formats: list[dict[str, Any]]) -> list[ResolvedQuality]:
    videos = [f for f in formats if is_video_format(f) and not is_drm(f) and f.get("ext") != "mhtml" and f.get("format_id")]
    audios = [f for f in formats if is_audio_only(f) and not is_drm(f) and f.get("format_id")]

    groups: dict[str, list[dict[str, Any]]] = {}
    for fmt in videos:
        hdr = (fmt.get("dynamic_range") or "SDR").upper() != "SDR"
        groups.setdefault(quality_id(int(fmt["height"]), fmt.get("fps"), hdr), []).append(fmt)

    resolved: list[ResolvedQuality] = []
    for ident, members in groups.items():
        best = min(members, key=lambda f: (_CODEC_RANK.get(_codec_family(f.get("vcodec")), 9), -(f.get("tbr") or 0)))
        height = int(best["height"])
        has_audio = best.get("acodec") not in (None, "none")
        audio = None if has_audio else _pick_audio(audios, best.get("ext") or "")
        container = _container(best.get("ext") or "mp4", None if audio is None else audio.get("ext"))
        selector = str(best["format_id"]) if audio is None else f"{best['format_id']}+{audio['format_id']}"
        sizes = [format_bytes(best)] + ([format_bytes(audio)] if audio else [])
        approx = sum(s for s in sizes if s) if all(sizes) else None
        option = QualityOption(
            id=ident,
            label=f"{height}p" + (str(_fps_bucket(best.get("fps"))) if (_fps_bucket(best.get("fps")) or 0) > 30 else ""),
            tier=TIERS.get(height),
            height=height,
            width=best.get("width"),
            fps=best.get("fps"),
            hdr=ident.endswith("-hdr"),
            container=container,
            video_codec=_codec_family(best.get("vcodec")) or None,
            audio_codec=_codec_family((audio or best).get("acodec")) or None,
            approx_bytes=approx,
            requires_merge=audio is not None,
        )
        resolved.append(ResolvedQuality(option, selector, container if audio is not None else None))

    resolved.sort(key=lambda r: (r.option.height, r.option.fps or 0, not r.option.hdr), reverse=True)
    return resolved


def build_quality_options(formats: list[dict[str, Any]]) -> list[QualityOption]:
    return [r.option for r in resolve_all(formats)]


def resolve_quality(formats: list[dict[str, Any]], wanted: str) -> ResolvedQuality:
    for candidate in resolve_all(formats):
        if candidate.option.id == wanted:
            return candidate
    raise AppError(ErrorCode.QUALITY_UNAVAILABLE)
