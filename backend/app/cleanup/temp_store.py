"""Temporary, self-cleaning storage for in-flight media.

Safeguards (layered on purpose, none is trusted alone):
* per-job directories with server-generated names only,
* path containment checks for every path handed out,
* cleanup on success, failure and cancellation (callers),
* a startup purge of anything left by a previous process,
* a periodic TTL sweep as the final safety net,
* a purge on graceful shutdown.
"""

from __future__ import annotations

import logging
import re
import shutil
import time
from pathlib import Path
from typing import Callable

from app.core.errors import AppError, ErrorCode

logger = logging.getLogger(__name__)

JOB_DIR_PREFIX = "mr-job-"
_JOB_ID = re.compile(r"^[a-f0-9]{32}$")
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$")


class TempStore:
    def __init__(self, root: Path, ttl_seconds: int, clock: Callable[[], float] = time.time) -> None:
        self.root = Path(root)
        self.ttl_seconds = ttl_seconds
        self._clock = clock

    def ensure_root(self) -> None:
        try:
            self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        except OSError as exc:
            raise AppError(ErrorCode.STORAGE_ERROR, internal_detail=str(exc)) from exc

    def _resolved_root(self) -> Path:
        return self.root.resolve()

    def job_dir(self, job_id: str) -> Path:
        if not _JOB_ID.match(job_id):
            raise AppError(ErrorCode.JOB_NOT_FOUND)
        return self.root / f"{JOB_DIR_PREFIX}{job_id}"

    def create_job_dir(self, job_id: str) -> Path:
        self.ensure_root()
        path = self.job_dir(job_id)
        try:
            path.mkdir(mode=0o700)
        except FileExistsError:
            pass
        except OSError as exc:
            raise AppError(ErrorCode.STORAGE_ERROR, internal_detail=str(exc)) from exc
        return path

    def file_path(self, job_dir: Path, filename: str) -> Path:
        """Return a contained path for a server-generated filename."""
        if not _SAFE_NAME.match(filename) or ".." in filename:
            raise AppError(ErrorCode.PROCESSING_ERROR, internal_detail=f"unsafe temp filename {filename!r}")
        candidate = (job_dir / filename).resolve()
        if not self._is_contained(candidate):
            raise AppError(ErrorCode.PROCESSING_ERROR, internal_detail="temp path escaped root")
        return candidate

    def _is_contained(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self._resolved_root())
            return True
        except (ValueError, OSError):
            return False

    def remove(self, path: Path | None) -> bool:
        """Delete a job directory or file inside the root. Never raises."""
        if path is None:
            return False
        try:
            target = Path(path)
            if not target.exists() or not self._is_contained(target) or target.resolve() == self._resolved_root():
                return False
            if target.is_dir():
                shutil.rmtree(target, ignore_errors=True)
            else:
                target.unlink(missing_ok=True)
            return not target.exists()
        except OSError:
            logger.warning("temp cleanup failed", exc_info=True)
            return False

    def _job_entries(self) -> list[Path]:
        if not self.root.exists():
            return []
        return [p for p in self.root.iterdir() if p.name.startswith(JOB_DIR_PREFIX)]

    def purge_all(self) -> int:
        """Remove every job directory (startup/shutdown)."""
        removed = sum(1 for entry in self._job_entries() if self.remove(entry))
        if removed:
            logger.info("purged %d abandoned temp entries", removed)
        return removed

    def sweep_expired(self) -> int:
        """Remove job directories older than the TTL."""
        cutoff = self._clock() - self.ttl_seconds
        removed = 0
        for entry in self._job_entries():
            try:
                if entry.stat().st_mtime < cutoff and self.remove(entry):
                    removed += 1
            except OSError:
                continue
        if removed:
            logger.info("ttl sweep removed %d temp entries", removed)
        return removed
