import pytest

from app.core.errors import ERROR_SPECS, AppError, ErrorCode
from app.services.ytdlp_errors import map_retrieval_error


@pytest.mark.parametrize("message, platform, code", [
    ("ERROR: [youtube] abc: Private video. Sign in if you've been granted access", "youtube", ErrorCode.PRIVATE_CONTENT),
    ("ERROR: [youtube] abc: Sign in to confirm you're not a bot. Use --cookies-from-browser", "youtube", ErrorCode.UPSTREAM_BLOCKED),
    ("ERROR: [youtube] abc: Sign in to confirm your age.", "youtube", ErrorCode.LOGIN_REQUIRED),
    ("ERROR: [youtube] abc: Video unavailable. This video has been removed by the uploader", "youtube", ErrorCode.CONTENT_DELETED),
    ("ERROR: [youtube] abc: Video unavailable", "youtube", ErrorCode.CONTENT_UNAVAILABLE),
    ("ERROR: [Instagram] abc: Requested content is not available, rate-limit reached or login required", "instagram", ErrorCode.LOGIN_REQUIRED),
    ("ERROR: [Instagram] abc: There is no video in this post", "instagram", ErrorCode.UNSUPPORTED_BY_PROVIDER),
    ("ERROR: [TikTok] 123: HTTP Error 429: Too Many Requests", "tiktok", ErrorCode.UPSTREAM_RATE_LIMITED),
    ("ERROR: Unsupported URL: https://example.com", None, ErrorCode.UNSUPPORTED_URL),
    ("ERROR: This video is DRM protected", "youtube", ErrorCode.DRM_PROTECTED),
    ("ERROR: Requested format is not available", "youtube", ErrorCode.QUALITY_UNAVAILABLE),
    ("ERROR: unable to download video data: <urlopen error timed out>", "tiktok", ErrorCode.UPSTREAM_TIMEOUT),
    ("ERROR: Unable to download webpage: Connection reset by peer", "tiktok", ErrorCode.NETWORK_ERROR),
    ("something nobody anticipated", None, ErrorCode.RETRIEVAL_FAILED),
])
def test_engine_messages_map_to_precise_codes(message, platform, code):
    assert map_retrieval_error(message, platform=platform).code is code


def test_every_code_has_user_copy_and_payload_hides_internals():
    for code in ErrorCode:
        spec = ERROR_SPECS[code]
        assert spec.title and spec.message and spec.message != "Something went wrong."
    err = AppError(ErrorCode.RETRIEVAL_FAILED, internal_detail="/tmp/secret/path Traceback")
    payload = err.to_payload("req123")["error"]
    assert payload["request_id"] == "req123" and payload["retryable"] is True
    assert "/tmp" not in str(payload) and "Traceback" not in str(payload)
