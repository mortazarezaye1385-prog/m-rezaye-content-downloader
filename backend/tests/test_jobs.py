import pytest

from app.core.errors import AppError, ErrorCode
from app.processors.jobs import JobManager, JobStatus, can_transition, public_view


def test_happy_path_transitions():
    jobs = JobManager(max_active=2)
    job = jobs.create()
    for status in [JobStatus.PREPARING, JobStatus.DOWNLOADING, JobStatus.PROCESSING, JobStatus.READY, JobStatus.TRANSFERRING, JobStatus.COMPLETED]:
        assert jobs.transition(job, status), status
    assert not jobs.transition(job, JobStatus.DOWNLOADING)  # terminal


def test_illegal_transitions_are_rejected():
    assert not can_transition(JobStatus.QUEUED, JobStatus.READY)
    assert not can_transition(JobStatus.COMPLETED, JobStatus.FAILED)
    assert not can_transition(JobStatus.CANCELLED, JobStatus.READY)
    assert can_transition(JobStatus.DOWNLOADING, JobStatus.CANCELLED)


def test_progress_view_is_honest():
    jobs = JobManager(max_active=2)
    job = jobs.create()
    view = public_view(job)
    assert view["progress"]["determinate"] is False and view["progress"]["percent"] is None
    jobs.update_progress(job, done=50, total=200)
    assert public_view(job)["progress"]["percent"] == 25.0
    jobs.update_progress(job, done=500)
    assert public_view(job)["progress"]["percent"] == 100.0


def test_concurrency_limit_and_cancel():
    jobs = JobManager(max_active=1)
    job = jobs.create()
    with pytest.raises(AppError) as busy:
        jobs.create()
    assert busy.value.code is ErrorCode.SERVER_BUSY
    jobs.cancel(job.id)
    assert job.status is JobStatus.CANCELLED and job.cancel_event.is_set()
    jobs.create()  # slot freed
    with pytest.raises(AppError):
        jobs.get("missing")
