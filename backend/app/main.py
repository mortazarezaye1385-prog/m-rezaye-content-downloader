"""M.Rezaye Content Downloader API."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.middleware import GuardMiddleware
from app.api.routes import downloads, health, media
from app.api.state import AppState
from app.cleanup.sweeper import sweeper_loop
from app.cleanup.temp_store import TempStore
from app.core.config import Settings, get_settings
from app.core.errors import AppError, ErrorCode
from app.core.logging import configure_logging
from app.processors.executor import DownloadExecutor
from app.processors.jobs import JobManager
from app.security.rate_limit import TokenBucketLimiter
from app.security.tickets import TicketSigner
from app.services.registry import ServiceRegistry
from app.services.ytdlp_client import YtDlpClient

logger = logging.getLogger("app")


def build_state(settings: Settings, services: ServiceRegistry | None = None, engine: YtDlpClient | None = None) -> AppState:
    signer = TicketSigner(settings.secret_key)
    store = TempStore(settings.temp_dir, settings.temp_ttl_seconds)
    jobs = JobManager(max_active=settings.max_concurrent_jobs)
    engine = engine or YtDlpClient(settings)
    return AppState(
        settings=settings,
        signer=signer,
        store=store,
        jobs=jobs,
        services=services or ServiceRegistry.default(settings, signer),
        executor=DownloadExecutor(settings, store, jobs, engine),
        limiters={
            "analyze": TokenBucketLimiter(settings.rate_limit_analyze_per_minute),
            "download": TokenBucketLimiter(settings.rate_limit_download_per_minute),
            "general": TokenBucketLimiter(settings.rate_limit_general_per_minute),
        },
    )


def _request_id(request: Request) -> str | None:
    return request.scope.get("state", {}).get("request_id")


def create_app(settings: Settings | None = None, state: AppState | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging()
    runtime = state or build_state(settings)

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        runtime.store.ensure_root()
        runtime.store.purge_all()  # abandoned files from a previous run
        task = asyncio.create_task(sweeper_loop(settings, runtime.store, runtime.jobs))
        try:
            yield
        finally:
            task.cancel()
            for job in runtime.jobs.all_jobs():
                job.cancel_event.set()
            runtime.store.purge_all()

    app = FastAPI(
        title="M.Rezaye Content Downloader API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/api/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/api/openapi.json",
    )
    app.state.runtime = runtime

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["content-type", "x-request-id"],
        expose_headers=["content-disposition", "content-length", "x-request-id"],
        allow_credentials=False,
        max_age=600,
    )
    app.add_middleware(
        GuardMiddleware,
        limiters=runtime.limiters,
        max_body_bytes=settings.max_request_body_bytes,
        trust_proxy=settings.trust_proxy_headers,
        hsts=settings.is_production,
    )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        rid = _request_id(request)
        if exc.internal_detail:
            logger.info("request %s -> %s (%s)", rid, exc.code.value, exc.internal_detail)
        return JSONResponse(exc.to_payload(rid), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        err = AppError(ErrorCode.VALIDATION_ERROR)
        return JSONResponse(err.to_payload(_request_id(request)), status_code=err.status_code)

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = ErrorCode.JOB_NOT_FOUND if exc.status_code == 404 else ErrorCode.VALIDATION_ERROR
        err = AppError(code, "Not found." if exc.status_code == 404 else None)
        return JSONResponse(err.to_payload(_request_id(request)), status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        rid = _request_id(request)
        logger.exception("unhandled error for request %s", rid)
        err = AppError(ErrorCode.INTERNAL_ERROR)
        return JSONResponse(err.to_payload(rid), status_code=500)

    app.include_router(health.router)
    app.include_router(media.router)
    app.include_router(downloads.router)
    return app


app = create_app()
