"""Thin, policy-enforcing wrapper around the yt-dlp retrieval engine.

Policy baked in here (and not overridable by callers):
* no accounts, cookies, browser sessions or credentials,
* no geo-restriction bypass,
* no unplayable/DRM formats,
* hard size and socket-timeout limits,
* output filenames are always server generated.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Callable

from app.core.config import Settings
from app.core.errors import AppError, ErrorCode
from app.services.ytdlp_errors import map_retrieval_error

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int | None], None]


class DownloadCancelled(Exception):
    pass


def _load_engine():
    try:
        import yt_dlp  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - depends on install
        raise AppError(ErrorCode.PROVIDER_UNAVAILABLE, internal_detail="yt-dlp not installed") from exc
    return yt_dlp


class YtDlpClient:
    name = "yt-dlp public extractor"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _base_options(self) -> dict[str, Any]:
        return {
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "no_color": True,
            "cachedir": False,
            "socket_timeout": self._settings.network_timeout_seconds,
            "retries": 2,
            "fragment_retries": 2,
            "geo_bypass": False,
            "allow_unplayable_formats": False,
            "check_formats": False,
            "max_filesize": self._settings.max_download_bytes,
            "restrictfilenames": True,
            "windowsfilenames": True,
            "overwrites": True,
            "noplaylist": True,
            "playlist_items": f"1:{self._settings.max_bundle_items}",
            # Explicitly never authenticate.
            "cookiefile": None,
            "usenetrc": False,
            "username": None,
            "password": None,
        }

    def extract(self, url: str, *, platform: str, allow_playlist: bool = False) -> dict[str, Any]:
        engine = _load_engine()
        opts = self._base_options() | {"skip_download": True, "noplaylist": not allow_playlist}
        try:
            with engine.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return ydl.sanitize_info(info)
        except AppError:
            raise
        except Exception as exc:  # engine raises DownloadError/ExtractorError
            raise map_retrieval_error(str(exc), platform=platform) from exc

    def download(
        self,
        url: str,
        *,
        platform: str,
        out_dir: Path,
        stem: str,
        format_selector: str,
        playlist_index: int | None,
        merge_format: str | None,
        progress: ProgressCallback,
        cancel_event: threading.Event,
    ) -> Path:
        engine = _load_engine()
        per_file: dict[str, tuple[int, int | None]] = {}

        def hook(d: dict[str, Any]) -> None:
            if cancel_event.is_set():
                raise DownloadCancelled()
            if d.get("status") not in {"downloading", "finished"}:
                return
            key = str(d.get("tmpfilename") or d.get("filename") or "file")
            done = int(d.get("downloaded_bytes") or 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            per_file[key] = (done, int(total) if total else None)
            done_sum = sum(v[0] for v in per_file.values())
            totals = [v[1] for v in per_file.values()]
            total_sum = sum(t for t in totals if t) if all(totals) else None
            progress(done_sum, total_sum)

        opts = self._base_options() | {
            "format": format_selector,
            "outtmpl": {"default": str(out_dir / f"{stem}.%(ext)s")},
            "paths": {"home": str(out_dir), "temp": str(out_dir)},
            "progress_hooks": [hook],
            "noplaylist": playlist_index is None,
        }
        if playlist_index is not None:
            opts["playlist_items"] = str(playlist_index)
        if merge_format:
            # Stream copy only: yt-dlp's merger remuxes without re-encoding.
            opts["merge_output_format"] = merge_format
        try:
            with engine.YoutubeDL(opts) as ydl:
                ydl.download([url])
        except DownloadCancelled:
            raise
        except Exception as exc:
            if cancel_event.is_set():
                raise DownloadCancelled() from exc
            raise map_retrieval_error(str(exc), platform=platform) from exc
        produced = sorted(p for p in out_dir.glob(f"{stem}.*") if not p.name.endswith((".part", ".ytdl", ".temp")))
        if not produced:
            raise AppError(ErrorCode.RETRIEVAL_FAILED, internal_detail="engine produced no file")
        return max(produced, key=lambda p: p.stat().st_size)
