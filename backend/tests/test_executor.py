import asyncio

from app.cleanup.temp_store import TempStore
from app.core.errors import AppError, ErrorCode
from app.processors.executor import DownloadExecutor
from app.processors.jobs import JobManager, JobStatus
from app.security.url_validation import Platform
from app.services.base import DownloadPlan, PlanStep
from tests.fakes import FakeEngine, make_settings

URL = "https://www.instagram.com/p/C1a2B3c4D5e/"


def setup(tmp_path, engine):
    settings = make_settings(tmp_path)
    store = TempStore(settings.temp_dir, 60)
    jobs = JobManager(max_active=3)
    return store, jobs, DownloadExecutor(settings, store, jobs, engine)


def steps(n):
    return [PlanStep(method="engine", source_url=URL, ext="mp4", format_selector="b", playlist_index=i + 1) for i in range(n)]


def test_single_download_ready_with_real_progress(tmp_path):
    store, jobs, ex = setup(tmp_path, FakeEngine())
    job = jobs.create()
    asyncio.run(ex.run(job, DownloadPlan(Platform.INSTAGRAM, "My Post", steps(1))))
    assert job.status is JobStatus.READY
    assert job.file_path.exists() and job.bytes_done == job.bytes_total == 2048
    assert job.filename == "mr-instagram-my-post.mp4"


def test_bundle_partial_failure_zips_successes(tmp_path):
    store, jobs, ex = setup(tmp_path, FakeEngine(fail_indexes={2}))
    job = jobs.create(items_total=3)
    asyncio.run(ex.run(job, DownloadPlan(Platform.INSTAGRAM, "Trip", steps(3), bundle=True)))
    assert job.status is JobStatus.READY and job.file_path.name == "bundle.zip"
    assert job.notice == "2 of 3 items were processed successfully."
    assert sorted(p.name for p in job.job_dir.iterdir()) == ["bundle.zip"]  # item files removed


def test_failure_cleans_up(tmp_path):
    store, jobs, ex = setup(tmp_path, FakeEngine(error=AppError(ErrorCode.NETWORK_ERROR)))
    job = jobs.create()
    asyncio.run(ex.run(job, DownloadPlan(Platform.INSTAGRAM, "x", steps(1))))
    assert job.status is JobStatus.FAILED and job.error.code is ErrorCode.NETWORK_ERROR
    assert not job.job_dir.exists()


def test_all_items_failing_is_a_failure(tmp_path):
    store, jobs, ex = setup(tmp_path, FakeEngine(fail_indexes={1, 2}))
    job = jobs.create(items_total=2)
    asyncio.run(ex.run(job, DownloadPlan(Platform.INSTAGRAM, "x", steps(2), bundle=True)))
    assert job.status is JobStatus.FAILED and not job.job_dir.exists()


def test_cancellation_cleans_up(tmp_path):
    store, jobs, ex = setup(tmp_path, FakeEngine())
    job = jobs.create()
    jobs.cancel(job.id)
    asyncio.run(ex.run(job, DownloadPlan(Platform.INSTAGRAM, "x", steps(1))))
    assert job.status is JobStatus.CANCELLED
    assert job.job_dir is None or not job.job_dir.exists()
