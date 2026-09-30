"""Application settings loaded from environment variables.

Only stdlib + pydantic are used so configuration is importable in any context
(tests, workers, CLI) without extra dependencies.
"""

from __future__ import annotations

import os
import secrets
import tempfile
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

MB = 1024 * 1024


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw and raw.strip() else default


def _env_list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if not raw:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings(BaseModel):
    environment: str = "development"
    # Used to sign short-lived download/preview tickets. If unset a random
    # per-process key is generated (tickets then die on restart, which is fine).
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    cors_origins: list[str] = ["http://localhost:3000"]
    trust_proxy_headers: bool = False

    temp_dir: Path = Path(tempfile.gettempdir()) / "mr-content-downloader"
    temp_ttl_seconds: int = 15 * 60
    cleanup_interval_seconds: int = 60
    delivered_job_grace_seconds: int = 90

    max_download_bytes: int = 2048 * MB
    max_preview_bytes: int = 8 * MB
    max_request_body_bytes: int = 64 * 1024
    max_concurrent_jobs: int = 3
    max_bundle_items: int = 30

    extraction_timeout_seconds: int = 45
    network_timeout_seconds: int = 20
    job_timeout_seconds: int = 30 * 60
    ticket_ttl_seconds: int = 30 * 60

    rate_limit_analyze_per_minute: int = 20
    rate_limit_download_per_minute: int = 10
    rate_limit_general_per_minute: int = 240

    # Optional official provider: Instagram API (own professional account only).
    instagram_graph_access_token: str | None = None
    instagram_graph_user_id: str | None = None
    instagram_graph_api_version: str = "v21.0"
    instagram_graph_max_pages: int = 5

    @field_validator("temp_ttl_seconds", "cleanup_interval_seconds", "max_concurrent_jobs")
    @classmethod
    def _positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be positive")
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def instagram_graph_enabled(self) -> bool:
        return bool(self.instagram_graph_access_token and self.instagram_graph_user_id)

    @classmethod
    def from_env(cls) -> "Settings":
        values: dict[str, object] = {
            "environment": os.getenv("APP_ENV", "development"),
            "cors_origins": _env_list("CORS_ORIGINS", ["http://localhost:3000"]),
            "trust_proxy_headers": _env_bool("TRUST_PROXY_HEADERS", False),
            "temp_ttl_seconds": _env_int("TEMP_TTL_SECONDS", 15 * 60),
            "cleanup_interval_seconds": _env_int("CLEANUP_INTERVAL_SECONDS", 60),
            "max_download_bytes": _env_int("MAX_DOWNLOAD_MB", 2048) * MB,
            "max_concurrent_jobs": _env_int("MAX_CONCURRENT_JOBS", 3),
            "max_bundle_items": _env_int("MAX_BUNDLE_ITEMS", 30),
            "extraction_timeout_seconds": _env_int("EXTRACTION_TIMEOUT_SECONDS", 45),
            "network_timeout_seconds": _env_int("NETWORK_TIMEOUT_SECONDS", 20),
            "rate_limit_analyze_per_minute": _env_int("RATE_LIMIT_ANALYZE_PER_MINUTE", 20),
            "rate_limit_download_per_minute": _env_int("RATE_LIMIT_DOWNLOAD_PER_MINUTE", 10),
            "instagram_graph_access_token": os.getenv("INSTAGRAM_GRAPH_ACCESS_TOKEN") or None,
            "instagram_graph_user_id": os.getenv("INSTAGRAM_GRAPH_USER_ID") or None,
        }
        if os.getenv("SECRET_KEY"):
            values["secret_key"] = os.environ["SECRET_KEY"]
        if os.getenv("TEMP_DIR"):
            values["temp_dir"] = Path(os.environ["TEMP_DIR"])
        return cls(**values)


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
