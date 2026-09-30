"""In-memory download job registry with an explicit state machine.

Jobs hold only transient data (progress counters and a temp file path). They
are never persisted and expire automatically.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from app.core.errors import AppError, ErrorCode


class JobStatus(str, Enum):
    QUEUED = "queued"
    PREPARING = "preparing"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    READY = "ready"
    TRANSFERRING = "transferring"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


TERMINAL = frozenset({JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.EXPIRED})
_FAIL_EXITS = {JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.EXPIRED}

TRANSITIONS: dict[JobStatus, frozenset[JobStatus]] = {
    JobStatus.QUEUED: frozenset({JobStatus.PREPARING} | _FAIL_EXITS),
    JobStatus.PREPARING: frozenset({JobStatus.DOWNLOADING, JobStatus.PROCESSING, JobStatus.READY} | _FAIL_EXITS),
    JobStatus.DOWNLOADING: frozenset({JobStatus.DOWNLOADING, JobStatus.PREPARING, JobStatus.PROCESSING, JobStatus.READY} | _FAIL_EXITS),
    JobStatus.PROCESSING: frozenset({JobStatus.READY} | _FAIL_EXITS),
    JobStatus.READY: frozenset({JobStatus.TRANSFERRING} | _FAIL_EXITS),
    JobStatus.TRANSFERRING: frozenset({JobStatus.COMPLETED} | _FAIL_EXITS),
    JobStatus.COMPLETED: frozenset(),
    JobStatus.FAILED: frozenset(),
    JobStatus.CANCELLED: frozenset(),
    JobStatus.EXPIRED: frozenset(),
}


def can_transition(current: JobStatus, target: JobStatus) -> bool:
    return target in TRANSITIONS[current]


@dataclass
class Job:
    id: str
    created_at: float
    updated_at: float
    status: JobStatus = JobStatus.QUEUED
    bytes_done: int = 0
    bytes_total: int | None = None
    items_total: int = 1
    items_succeeded: int = 0
    items_failed: int = 0
    filename: str | None = None
    content_type: str = "application/octet-stream"
    file_path: Path | None = None
    job_dir: Path | None = None
    error: AppError | None = None
    notice: str | None = None
    cancel_event: threading.Event = field(default_factory=threading.Event)


class JobManager:
    def __init__(self, *, max_active: int, clock: Callable[[], float] = time.time) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.RLock()
        self._max_active = max_active
        self._clock = clock

    def active_count(self) -> int:
        with self._lock:
            return sum(1 for j in self._jobs.values() if j.status not in TERMINAL and j.status is not JobStatus.READY)

    def create(self, *, items_total: int = 1) -> Job:
        with self._lock:
            if self.active_count() >= self._max_active:
                raise AppError(ErrorCode.SERVER_BUSY)
            now = self._clock()
            job = Job(id=uuid.uuid4().hex, created_at=now, updated_at=now, items_total=items_total)
            self._jobs[job.id] = job
            return job

    def get(self, job_id: str) -> Job:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise AppError(ErrorCode.JOB_NOT_FOUND)
            return job

    def transition(self, job: Job, target: JobStatus, *, error: AppError | None = None) -> bool:
        with self._lock:
            if not can_transition(job.status, target):
                return False
            job.status = target
            job.updated_at = self._clock()
            if error is not None:
                job.error = error
            return True

    def update_progress(self, job: Job, *, done: int | None = None, total: int | None = None) -> None:
        with self._lock:
            if done is not None:
                job.bytes_done = max(0, done)
            if total is not None and total > 0:
                job.bytes_total = total
            job.updated_at = self._clock()

    def cancel(self, job_id: str) -> Job:
        job = self.get(job_id)
        job.cancel_event.set()
        self.transition(job, JobStatus.CANCELLED, error=AppError(ErrorCode.CANCELLED))
        return job

    def remove(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.pop(job_id, None)

    def reap(self, *, max_age_seconds: int, terminal_grace_seconds: int) -> list[Job]:
        """Drop old jobs. Returns removed jobs so callers can delete their files."""
        now = self._clock()
        removed: list[Job] = []
        with self._lock:
            for job_id, job in list(self._jobs.items()):
                expired = now - job.created_at > max_age_seconds
                finished = job.status in TERMINAL and now - job.updated_at > terminal_grace_seconds
                if expired or finished:
                    if job.status not in TERMINAL:
                        job.cancel_event.set()
                        job.status = JobStatus.EXPIRED
                    removed.append(self._jobs.pop(job_id))
        return removed

    def all_jobs(self) -> list[Job]:
        with self._lock:
            return list(self._jobs.values())


def public_view(job: Job) -> dict[str, Any]:
    total = job.bytes_total
    percent = None
    if total and total > 0:
        percent = round(min(100.0, job.bytes_done * 100.0 / total), 1)
    return {
        "id": job.id,
        "status": job.status.value,
        "progress": {
            "bytes_done": job.bytes_done,
            "bytes_total": total,
            "percent": percent,
            "determinate": percent is not None,
        },
        "items": {"total": job.items_total, "succeeded": job.items_succeeded, "failed": job.items_failed},
        "filename": job.filename,
        "notice": job.notice,
        "error": None if job.error is None else job.error.to_payload(None)["error"],
    }
