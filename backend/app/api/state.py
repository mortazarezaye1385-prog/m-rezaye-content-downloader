"""Process-wide runtime objects, created once in the app lifespan."""

from __future__ import annotations

from dataclasses import dataclass

from app.cleanup.temp_store import TempStore
from app.core.config import Settings
from app.processors.executor import DownloadExecutor
from app.processors.jobs import JobManager
from app.security.rate_limit import TokenBucketLimiter
from app.security.tickets import TicketSigner
from app.services.registry import ServiceRegistry


@dataclass
class AppState:
    settings: Settings
    signer: TicketSigner
    store: TempStore
    jobs: JobManager
    services: ServiceRegistry
    executor: DownloadExecutor
    limiters: dict[str, TokenBucketLimiter]
