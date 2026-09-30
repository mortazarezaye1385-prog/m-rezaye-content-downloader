"""Runs a DownloadPlan for one job: retrieve -> (merge/zip) -> ready.

Temporary files are removed on failure and cancellation here; delivery removes
them after streaming; the TTL sweeper catches anything left behind.
"""

from __future__ import annotations

import asyncio
import logging
import mimetypes
from pathlib import Path

from app.cleanup.temp_store import TempStore
from app.core.config import Settings
from app.core.errors import AppError, ErrorCode
from app.processors.archive import build_archive
from app.processors.jobs import Job, JobManager, JobStatus
from app.services.base import DownloadPlan, PlanStep
from app.services.ytdlp_client import DownloadCancelled, YtDlpClient
from app.utils.filenames import build_download_name, safe_extension
from app.utils.http import stream_media

logger = logging.getLogger(__name__)


class DownloadExecutor:
    def __init__(self, settings: Settings, store: TempStore, jobs: JobManager, engine: YtDlpClient) -> None:
        self.settings = settings
        self.store = store
        self.jobs = jobs
        self.engine = engine

    async def run(self, job: Job, plan: DownloadPlan) -> None:
        try:
            await asyncio.wait_for(self._run(job, plan), timeout=self.settings.job_timeout_seconds)
        except asyncio.TimeoutError:
            job.cancel_event.set()
            self._fail(job, AppError(ErrorCode.UPSTREAM_TIMEOUT))
        except (DownloadCancelled, asyncio.CancelledError):
            self.jobs.transition(job, JobStatus.CANCELLED, error=AppError(ErrorCode.CANCELLED))
            self.store.remove(job.job_dir)
        except AppError as err:
            self._fail(job, err)
        except OSError as exc:
            self._fail(job, AppError(ErrorCode.STORAGE_ERROR, internal_detail=str(exc)))
        except Exception as exc:  # noqa: BLE001 - last-resort guard, details logged only
            logger.exception("job %s crashed", job.id)
            self._fail(job, AppError(ErrorCode.PROCESSING_ERROR, internal_detail=repr(exc)))

    def _fail(self, job: Job, err: AppError) -> None:
        if err.internal_detail:
            logger.warning("job %s failed: %s (%s)", job.id, err.code.value, err.internal_detail)
        self.jobs.transition(job, JobStatus.FAILED, error=err)
        self.store.remove(job.job_dir)

    def _check_cancel(self, job: Job) -> None:
        if job.cancel_event.is_set() or job.status is JobStatus.CANCELLED:
            raise DownloadCancelled()

    async def _run(self, job: Job, plan: DownloadPlan) -> None:
        job.job_dir = self.store.create_job_dir(job.id)
        self.jobs.transition(job, JobStatus.PREPARING)
        known = [s.expected_bytes for s in plan.steps]
        if all(known):
            self.jobs.update_progress(job, total=sum(known))  # type: ignore[arg-type]

        produced: list[tuple[Path, str]] = []
        base_done = 0
        for index, step in enumerate(plan.steps):
            self._check_cancel(job)
            try:
                path, size = await self._run_step(job, step, index, base_done, len(plan.steps) == 1)
            except (DownloadCancelled, asyncio.CancelledError):
                raise
            except AppError as err:
                if not plan.bundle:
                    raise
                job.items_failed += 1
                logger.info("bundle item %d failed: %s", index, err.code.value)
                continue
            base_done += size
            job.items_succeeded += 1
            arcname = build_download_name(plan.platform.value, plan.title, path.suffix.lstrip("."), index if plan.bundle else None)
            produced.append((path, arcname))

        self._check_cancel(job)
        if not produced:
            raise AppError(ErrorCode.RETRIEVAL_FAILED, "None of the items could be retrieved.")

        if plan.bundle:
            self.jobs.transition(job, JobStatus.PROCESSING)
            archive = self.store.file_path(job.job_dir, "bundle.zip")
            size = await asyncio.to_thread(build_archive, produced, archive)
            for path, _ in produced:
                self.store.remove(path)
            job.file_path = archive
            job.filename = build_download_name(plan.platform.value, plan.title, "zip")
            job.content_type = "application/zip"
            if job.items_failed:
                job.notice = f"{job.items_succeeded} of {job.items_total} items were processed successfully."
        else:
            path, name = produced[0]
            size = path.stat().st_size
            job.file_path = path
            job.filename = name
            job.content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"

        self.jobs.update_progress(job, done=size, total=size)
        if not self.jobs.transition(job, JobStatus.READY):
            self.store.remove(job.job_dir)

    async def _run_step(self, job: Job, step: PlanStep, index: int, base_done: int, single: bool) -> tuple[Path, int]:
        stem = f"item-{index + 1:02d}"
        assert job.job_dir is not None
        if step.method == "direct" and step.direct_url:
            path = self.store.file_path(job.job_dir, f"{stem}.{safe_extension(step.ext, 'bin')}")
            return path, await self._direct(job, step.direct_url, path, base_done)

        def progress(done: int, total: int | None) -> None:
            if job.status is JobStatus.PREPARING:
                self.jobs.transition(job, JobStatus.DOWNLOADING)
            new_total = (base_done + total) if (single and total) else None
            if new_total is not None and job.bytes_total and new_total < job.bytes_total:
                new_total = None  # keep the larger, plan-level estimate (video+audio)
            self.jobs.update_progress(job, done=base_done + done, total=new_total)

        def call() -> Path:
            return self.engine.download(
                step.source_url,
                platform=job_platform(step),
                out_dir=job.job_dir,  # type: ignore[arg-type]
                stem=stem,
                format_selector=step.format_selector or "best",
                playlist_index=step.playlist_index,
                merge_format=step.merge_format,
                progress=progress,
                cancel_event=job.cancel_event,
            )

        path = await asyncio.to_thread(call)
        return path, path.stat().st_size

    async def _direct(self, job: Job, url: str, path: Path, base_done: int) -> int:
        written = 0
        with open(path, "wb") as fh:
            async for chunk, length, _ctype in stream_media(url, timeout=self.settings.network_timeout_seconds, max_bytes=self.settings.max_download_bytes):
                self._check_cancel(job)
                if job.status is JobStatus.PREPARING:
                    self.jobs.transition(job, JobStatus.DOWNLOADING)
                fh.write(chunk)
                written += len(chunk)
                self.jobs.update_progress(job, done=base_done + written, total=(base_done + length) if (length and job.items_total == 1) else None)
        return written


def job_platform(step: PlanStep) -> str:
    host = step.source_url.split("/")[2] if "//" in step.source_url else ""
    for name in ("instagram", "tiktok", "youtube"):
        if name in host:
            return name
    return "unknown"
