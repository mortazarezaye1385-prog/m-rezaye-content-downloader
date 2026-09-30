import pytest

from app.core.errors import AppError, ErrorCode
from app.security.url_validation import Platform, UrlKind, parse_supported_url


@pytest.mark.parametrize(
    "raw, platform, kind, canonical",
    [
        ("https://www.instagram.com/p/C1a2B3c4D5e/", Platform.INSTAGRAM, UrlKind.INSTAGRAM_POST, "https://www.instagram.com/p/C1a2B3c4D5e/"),
        ("instagram.com/p/C1a2B3c4D5e?igsh=abc", Platform.INSTAGRAM, UrlKind.INSTAGRAM_POST, "https://www.instagram.com/p/C1a2B3c4D5e/"),
        ("https://www.instagram.com/someuser/p/C1a2B3c4D5e/", Platform.INSTAGRAM, UrlKind.INSTAGRAM_POST, "https://www.instagram.com/p/C1a2B3c4D5e/"),
        ("https://www.instagram.com/reel/C9zYxWvUtS1/?utm_source=ig", Platform.INSTAGRAM, UrlKind.INSTAGRAM_REEL, "https://www.instagram.com/reel/C9zYxWvUtS1/"),
        ("https://instagram.com/stories/highlights/17912345678901234/", Platform.INSTAGRAM, UrlKind.INSTAGRAM_HIGHLIGHT, "https://www.instagram.com/stories/highlights/17912345678901234/"),
        ("https://www.instagram.com/s/aGlnaGxpZ2h0OjE3OTEyMzQ1Njc4OTAxMjM0?story_media_id=1", Platform.INSTAGRAM, UrlKind.INSTAGRAM_HIGHLIGHT, "https://www.instagram.com/stories/highlights/17912345678901234/"),
        ("https://www.tiktok.com/@some.user/video/7301234567890123456?is_from_webapp=1", Platform.TIKTOK, UrlKind.TIKTOK_VIDEO, "https://www.tiktok.com/@some.user/video/7301234567890123456"),
        ("https://www.tiktok.com/@some.user/photo/7301234567890123456", Platform.TIKTOK, UrlKind.TIKTOK_PHOTO, "https://www.tiktok.com/@some.user/photo/7301234567890123456"),
        ("https://vm.tiktok.com/ZMabc123/", Platform.TIKTOK, UrlKind.TIKTOK_SHORT_LINK, "https://vm.tiktok.com/ZMabc123/"),
        ("https://youtu.be/dQw4w9WgXcQ?si=xyz", Platform.YOUTUBE, UrlKind.YOUTUBE_VIDEO, "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
        ("https://m.youtube.com/watch?v=dQw4w9WgXcQ&t=42", Platform.YOUTUBE, UrlKind.YOUTUBE_VIDEO, "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
        ("https://www.youtube.com/shorts/abcdefghijk", Platform.YOUTUBE, UrlKind.YOUTUBE_SHORT, "https://www.youtube.com/shorts/abcdefghijk"),
        ("http://youtube.com/live/abcdefghijk", Platform.YOUTUBE, UrlKind.YOUTUBE_VIDEO, "https://www.youtube.com/watch?v=abcdefghijk"),
    ],
)
def test_supported_urls(raw, platform, kind, canonical):
    parsed = parse_supported_url(raw)
    assert parsed.platform is platform
    assert parsed.kind is kind
    assert parsed.canonical_url == canonical


@pytest.mark.parametrize(
    "raw, code",
    [
        ("", ErrorCode.INVALID_URL),
        ("not a url", ErrorCode.INVALID_URL),
        ("javascript:alert(1)", ErrorCode.INVALID_URL),
        ("ftp://youtube.com/watch?v=dQw4w9WgXcQ", ErrorCode.INVALID_URL),
        ("https://user:pass@youtube.com/watch?v=dQw4w9WgXcQ", ErrorCode.INVALID_URL),
        ("https://youtube.com:8080/watch?v=dQw4w9WgXcQ", ErrorCode.INVALID_URL),
        ("https://youtube.com.evil.example/watch?v=dQw4w9WgXcQ", ErrorCode.UNSUPPORTED_PLATFORM),
        ("https://evilyoutube.com/watch?v=dQw4w9WgXcQ", ErrorCode.UNSUPPORTED_PLATFORM),
        ("https://127.0.0.1/p/abc", ErrorCode.INVALID_URL),
        ("https://vimeo.com/12345", ErrorCode.UNSUPPORTED_PLATFORM),
        ("https://www.instagram.com/someuser/", ErrorCode.UNSUPPORTED_URL),
        ("https://www.tiktok.com/@someuser", ErrorCode.UNSUPPORTED_URL),
        ("https://www.youtube.com/watch?v=short", ErrorCode.INVALID_URL),
        ("https://www.youtube.com/playlist?list=PL123", ErrorCode.UNSUPPORTED_CONTENT_TYPE),
        ("https://www.youtube.com/@channel", ErrorCode.UNSUPPORTED_URL),
        ("https://www.instagram.com/s/bm90LWEtaGlnaGxpZ2h0", ErrorCode.UNSUPPORTED_URL),
        ("https://youtube.com/watch?v=dQw4w9WgXcQ" + "a" * 3000, ErrorCode.INVALID_URL),
    ],
)
def test_rejected_urls(raw, code):
    with pytest.raises(AppError) as info:
        parse_supported_url(raw)
    assert info.value.code is code


def test_platform_mismatch_is_explained():
    with pytest.raises(AppError) as info:
        parse_supported_url("https://youtu.be/dQw4w9WgXcQ", expected=Platform.TIKTOK)
    assert info.value.code is ErrorCode.UNSUPPORTED_PLATFORM
    assert "YouTube" in info.value.message
