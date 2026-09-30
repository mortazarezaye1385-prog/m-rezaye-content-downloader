"""Typed application errors with user-facing copy.

Every failure the API can report is an ``ErrorCode``. The spec table holds the
HTTP status, a human title/message and whether retrying is sensible. Internal
details (paths, stack traces, upstream messages) never leave the server; they
are logged against the request id instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    INVALID_URL = "invalid_url"
    UNSUPPORTED_PLATFORM = "unsupported_platform"
    UNSUPPORTED_URL = "unsupported_url"
    UNSUPPORTED_CONTENT_TYPE = "unsupported_content_type"
    UNSUPPORTED_BY_PROVIDER = "unsupported_by_provider"
    PRIVATE_CONTENT = "private_content"
    LOGIN_REQUIRED = "login_required"
    CONTENT_UNAVAILABLE = "content_unavailable"
    CONTENT_DELETED = "content_deleted"
    DRM_PROTECTED = "drm_protected"
    NETWORK_ERROR = "network_error"
    UPSTREAM_TIMEOUT = "upstream_timeout"
    UPSTREAM_RATE_LIMITED = "upstream_rate_limited"
    UPSTREAM_BLOCKED = "upstream_blocked"
    RATE_LIMITED = "rate_limited"
    RETRIEVAL_FAILED = "retrieval_failed"
    QUALITY_UNAVAILABLE = "quality_unavailable"
    MEDIA_TOO_LARGE = "media_too_large"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    INVALID_TICKET = "invalid_ticket"
    TICKET_EXPIRED = "ticket_expired"
    JOB_NOT_FOUND = "job_not_found"
    JOB_NOT_READY = "job_not_ready"
    SERVER_BUSY = "server_busy"
    CANCELLED = "cancelled"
    REQUEST_TOO_LARGE = "request_too_large"
    VALIDATION_ERROR = "validation_error"
    PROCESSING_ERROR = "processing_error"
    STORAGE_ERROR = "storage_error"
    INTERNAL_ERROR = "internal_error"


@dataclass(frozen=True)
class ErrorSpec:
    status: int
    title: str
    message: str
    retryable: bool = False


ERROR_SPECS: dict[ErrorCode, ErrorSpec] = {
    ErrorCode.INVALID_URL: ErrorSpec(422, "Invalid URL", "That doesn't look like a valid link. Check it and paste it again."),
    ErrorCode.UNSUPPORTED_PLATFORM: ErrorSpec(422, "Unsupported platform", "Only Instagram, TikTok and YouTube links are supported."),
    ErrorCode.UNSUPPORTED_URL: ErrorSpec(422, "Unsupported link", "This kind of link isn't supported. Paste a direct link to a post, video or highlight."),
    ErrorCode.UNSUPPORTED_CONTENT_TYPE: ErrorSpec(422, "Unsupported content type", "This content type can't be processed by the supported retrieval method."),
    ErrorCode.UNSUPPORTED_BY_PROVIDER: ErrorSpec(422, "Not supported by the current retrieval method", "The platform doesn't expose this content through the retrieval method this app uses. No workaround is attempted."),
    ErrorCode.PRIVATE_CONTENT: ErrorSpec(403, "Private content", "This content is not publicly accessible through the supported retrieval method."),
    ErrorCode.LOGIN_REQUIRED: ErrorSpec(403, "Sign-in required by the platform", "The platform only shows this content to signed-in users. This app never uses accounts, cookies or session tokens, so it can't be retrieved."),
    ErrorCode.CONTENT_UNAVAILABLE: ErrorSpec(404, "Content unavailable", "The content couldn't be found. It may be unavailable in this region or no longer public."),
    ErrorCode.CONTENT_DELETED: ErrorSpec(410, "Content removed", "This content has been deleted or removed by the platform."),
    ErrorCode.DRM_PROTECTED: ErrorSpec(422, "Protected content", "This media is DRM-protected. Protected media is never processed."),
    ErrorCode.NETWORK_ERROR: ErrorSpec(502, "Network problem", "The platform couldn't be reached. Check the connection and try again.", True),
    ErrorCode.UPSTREAM_TIMEOUT: ErrorSpec(504, "Timed out", "The platform took too long to respond.", True),
    ErrorCode.UPSTREAM_RATE_LIMITED: ErrorSpec(429, "Platform rate limit", "The platform is limiting requests right now. Wait a minute and try again.", True),
    ErrorCode.UPSTREAM_BLOCKED: ErrorSpec(503, "Temporarily unavailable", "The platform refused the request for now (for example a bot check). This app won't try to get around it; try again later.", True),
    ErrorCode.RATE_LIMITED: ErrorSpec(429, "Slow down a little", "Too many requests in a short time. Wait a moment and try again.", True),
    ErrorCode.RETRIEVAL_FAILED: ErrorSpec(502, "Media retrieval failed", "The media couldn't be retrieved from the platform.", True),
    ErrorCode.QUALITY_UNAVAILABLE: ErrorSpec(409, "Quality unavailable", "That quality is no longer available. Please select another available quality."),
    ErrorCode.MEDIA_TOO_LARGE: ErrorSpec(413, "File too large", "This media is larger than the configured download limit."),
    ErrorCode.PROVIDER_UNAVAILABLE: ErrorSpec(503, "Retrieval engine unavailable", "The media retrieval engine isn't installed or configured on the server."),
    ErrorCode.INVALID_TICKET: ErrorSpec(400, "Invalid download request", "This download request isn't valid. Analyze the link again."),
    ErrorCode.TICKET_EXPIRED: ErrorSpec(410, "Analysis expired", "This analysis is too old. Analyze the link again to get fresh media.", True),
    ErrorCode.JOB_NOT_FOUND: ErrorSpec(404, "Download not found", "This download no longer exists. Temporary files are deleted automatically."),
    ErrorCode.JOB_NOT_READY: ErrorSpec(409, "Not ready yet", "The file is still being prepared.", True),
    ErrorCode.SERVER_BUSY: ErrorSpec(503, "Server busy", "Several downloads are already running. Try again in a moment.", True),
    ErrorCode.CANCELLED: ErrorSpec(409, "Cancelled", "The download was cancelled and its temporary files were removed."),
    ErrorCode.REQUEST_TOO_LARGE: ErrorSpec(413, "Request too large", "The request body is larger than allowed."),
    ErrorCode.VALIDATION_ERROR: ErrorSpec(422, "Invalid request", "Some request fields are missing or invalid."),
    ErrorCode.PROCESSING_ERROR: ErrorSpec(500, "Processing error", "The server couldn't finish processing this media.", True),
    ErrorCode.STORAGE_ERROR: ErrorSpec(507, "Temporary storage problem", "The server ran out of temporary space or couldn't write the file.", True),
    ErrorCode.INTERNAL_ERROR: ErrorSpec(500, "Unexpected server error", "The server hit an unexpected problem. Use the reference ID if it keeps happening.", True),
}


class AppError(Exception):
    """An error that is safe to show to the user."""

    def __init__(
        self,
        code: ErrorCode,
        message: str | None = None,
        *,
        title: str | None = None,
        retryable: bool | None = None,
        internal_detail: str | None = None,
    ) -> None:
        self.code = code
        spec = ERROR_SPECS[code]
        self.title = title or spec.title
        self.message = message or spec.message
        self.retryable = spec.retryable if retryable is None else retryable
        # Never serialized; for logs only.
        self.internal_detail = internal_detail
        super().__init__(f"{code.value}: {self.message}")

    @property
    def status_code(self) -> int:
        return ERROR_SPECS[self.code].status

    def to_payload(self, request_id: str | None) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code.value,
                "title": self.title,
                "message": self.message,
                "retryable": self.retryable,
                "request_id": request_id,
            }
        }
