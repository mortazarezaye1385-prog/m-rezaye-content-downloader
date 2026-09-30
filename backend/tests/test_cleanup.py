import os
import time

import pytest

from app.cleanup.sweeper import sweep_once
from app.cleanup.temp_store import TempStore
from app.core.errors import AppError
from app.processors.jobs import JobManager, JobStatus
from tests.fakes import make_settings

JOB = "a" * 32


def test_job_dir_and_containment(tmp_path):
    store = TempStore(tmp_path / "store", ttl_seconds=60)
    job_dir = store.create_job_dir(JOB)
    assert job_dir.name == f"mr-job-{JOB}"
    assert store.file_path(job_dir, "item-01.mp4").parent == job_dir.resolve()
    for bad in ["../../etc/passwd", "/abs.mp4", ".hidden", "a/b.mp4", "..."]:
        with pytest.raises(AppError):
            store.file_path(job_dir, bad)
    with pytest.raises(AppError):
        store.job_dir("../escape")


def test_remove_refuses_outside_root(tmp_path):
    store = TempStore(tmp_path / "store", ttl_seconds=60)
    store.ensure_root()
    outside = tmp_path / "keep.txt"
    outside.write_text("keep")
    assert store.remove(outside) is False
    assert outside.exists()
    assert store.remove(store.root) is False
    assert store.root.exists()


def test_startup_purge_only_touches_job_dirs(tmp_path):
    store = TempStore(tmp_path / "store", ttl_seconds=60)
    d = store.create_job_dir(JOB)
    (d / "item-01.mp4").write_bytes(b"x")
    other = store.root / "not-ours.txt"
    other.write_text("x")
    assert store.purge_all() == 1
    assert not d.exists()
    assert other.exists()


def test_ttl_sweep(tmp_path):
    now = time.time()
    store = TempStore(tmp_path / "store", ttl_seconds=60, clock=lambda: now)
    old = store.create_job_dir("b" * 32)
    fresh = store.create_job_dir("c" * 32)
    os.utime(old, (now - 120, now - 120))
    assert store.sweep_expired() == 1
    assert not old.exists() and fresh.exists()


def test_sweeper_reaps_stale_jobs_and_files(tmp_path):
    clock = {"t": 1000.0}
    settings = make_settings(tmp_path, temp_ttl_seconds=60)
    store = TempStore(settings.temp_dir, 60, clock=lambda: clock["t"])
    jobs = JobManager(max_active=3, clock=lambda: clock["t"])
    job = jobs.create()
    job.job_dir = store.create_job_dir(job.id)
    clock["t"] += 61
    sweep_once(settings, store, jobs)
    assert not job.job_dir.exists()
    assert job.status is JobStatus.EXPIRED and job.cancel_event.is_set()
