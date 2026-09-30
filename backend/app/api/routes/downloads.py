"""Download jobs: create -> poll progress -> fetch file once -> auto-delete."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse

from app.api.deps import get_state
from app.api.state import AppState
from app.core.errors import AppError, ErrorCode
from app.processors.jobs import JobStatus, public_view
from app.schemas.media import DownloadRequest
from app.security.url_validation import Platform, parse_supported_url
from app.services.base import TICKET_DOWNLOAD, TICKET_PREVIEW
from app.utils.filenames import content_disposition
from app.utils.http import stream_media

router = APIRouter(prefix="/api", tags=["downloads"])
CHUNK = 256 * 1024
NO_STORE = {"Cache-Control": "no-store"}


@router.post("/downloads", status_code=202)
async def create_download(body: DownloadRequest, state: AppState = Depends(get_state)) -> dict:
    ticket = state.signer.verify(body.ticket, purpose=TICKET_DOWNLOAD)
    try:
        platform = Platform(ticket.get("p"))
    except ValueError as exc:
        raise AppError(ErrorCode.INVALID_TICKET) from exc
    # Defence in depth: the ticket URL must still pass the allowlist.
    parse_supported_url(ticket.get("u", ""), expected=platform)
    plan = await state.services.get(platform).plan_download(ticket, body.quality_id)
    job = state.jobs.create(items_total=len(plan.steps))
    asyncio.create_task(state.executor.run(job, plan))
    return public_view(job)


@router.get("/downloads/{job_id}")
async def job_status(job_id: str, response: Response, state: AppState = Depends(get_state)) -> dict:
    response.headers.update(NO_STORE)
    return public_view(state.jobs.get(job_id))


@router.delete("/downloads/{job_id}")
async def cancel_job(job_id: str, state: AppState = Depends(get_state)) -> dict:
    job = state.jobs.cancel(job_id)
    if job.status is JobStatus.CANCELLED:
        state.store.remove(job.job_dir)
    return public_view(job)


@router.get("/downloads/{job_id}/file")
async def download_file(job_id: str, state: AppState = Depends(get_state)) -> StreamingResponse:
    job = state.jobs.get(job_id)
    if job.status in {JobStatus.TRANSFERRING, JobStatus.COMPLETED}:
        raise AppError(ErrorCode.JOB_NOT_FOUND, "This file was already delivered and has been deleted from the server.")
    if job.status is not JobStatus.READY or job.file_path is None:
        raise AppError(ErrorCode.JOB_NOT_READY)
    path = job.file_path
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise AppError(ErrorCode.JOB_NOT_FOUND, internal_detail=str(exc)) from exc
    state.jobs.transition(job, JobStatus.TRANSFERRING)
    state.jobs.update_progress(job, done=0, total=size)

    def body() -> Iterator[bytes]:
        sent = 0
        try:
            with open(path, "rb") as fh:
                while chunk := fh.read(CHUNK):
                    if job.cancel_event.is_set():
                        return
                    yield chunk
                    sent += len(chunk)
                    state.jobs.update_progress(job, done=sent)
        finally:
            state.store.remove(job.job_dir)
            if sent >= size:
                state.jobs.transition(job, JobStatus.COMPLETED)
            else:
                state.jobs.transition(job, JobStatus.FAILED, error=AppError(ErrorCode.NETWORK_ERROR, "The transfer to your device was interrupted. Start the download again."))

    headers = {
        "Content-Disposition": content_disposition(job.filename or "download.bin"),
        "Content-Length": str(size),
        **NO_STORE,
    }
    return StreamingResponse(body(), media_type=job.content_type, headers=headers)


@router.get("/preview")
async def preview(t: str = Query(min_length=10, max_length=8192), state: AppState = Depends(get_state)) -> Response:
    """Proxy a signed thumbnail so previews work despite CDN hotlink rules."""
    ticket = state.signer.verify(t, purpose=TICKET_PREVIEW)
    data = bytearray()
    ctype = "image/jpeg"
    async for chunk, _length, content_type in stream_media(ticket["u"], timeout=state.settings.network_timeout_seconds, max_bytes=state.settings.max_preview_bytes):
        if content_type:
            ctype = content_type.split(";")[0].strip()
        if not ctype.startswith("image/"):
            raise AppError(ErrorCode.RETRIEVAL_FAILED, internal_detail=f"preview not an image: {ctype}")
        data.extend(chunk)
    return Response(bytes(data), media_type=ctype, headers={"Cache-Control": "private, max-age=300"})
