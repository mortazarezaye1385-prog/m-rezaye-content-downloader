"""Background safety net: reap stale jobs and TTL-expired temp files."""

from __future__ import annotations

import asyncio
import logging

from app.cleanup.temp_store import TempStore
from app.core.config import Settings
from app.processors.jobs import JobManager

logger = logging.getLogger(__name__)


def sweep_once(settings: Settings, store: TempStore, jobs: JobManager) -> int:
    removed = 0
    for job in jobs.reap(max_age_seconds=settings.temp_ttl_seconds, terminal_grace_seconds=settings.delivered_job_grace_seconds):
        if store.remove(job.job_dir):
            removed += 1
    removed += store.sweep_expired()
    return removed


async def sweeper_loop(settings: Settings, store: TempStore, jobs: JobManager) -> None:
    while True:
        await asyncio.sleep(settings.cleanup_interval_seconds)
        try:
            await asyncio.to_thread(sweep_once, settings, store, jobs)
        except Exception:  # noqa: BLE001 - never let the safety net die
            logger.exception("cleanup sweep failed")
