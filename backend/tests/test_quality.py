import pytest

from app.core.errors import AppError, ErrorCode
from app.services.youtube.quality import build_quality_options, resolve_quality
from app.services.youtube.service import classify
from app.schemas.media import ContentType, Orientation
from app.security.url_validation import UrlKind
from app.services.media_utils import aspect_label, orientation_of
from tests.fakes import yt_formats


def test_only_real_qualities_are_listed():
    ids = [q.id for q in build_quality_options(yt_formats())]
    assert ids == ["2160p", "1080p60", "1080p", "720p"]  # no DRM 4320p, no storyboard, nothing invented


def test_tiers_and_merge_metadata():
    options = {q.id: q for q in build_quality_options(yt_formats())}
    assert options["2160p"].tier == "4K"
    assert options["1080p"].tier == "Full HD" and options["720p"].tier == "HD"
    assert options["1080p"].video_codec == "avc1" and options["1080p"].container == "mp4"
    assert options["1080p"].approx_bytes == 11_000 and options["1080p"].requires_merge
    assert options["2160p"].container == "webm"  # vp9 + opus, stream copy
    assert options["1080p60"].approx_bytes is None  # unknown stays unknown
    assert options["720p"].requires_merge is False  # progressive format already has audio


def test_resolve_quality_and_unavailable():
    chosen = resolve_quality(yt_formats(), "1080p")
    assert chosen.format_selector == "137+140" and chosen.merge_format == "mp4"
    assert resolve_quality(yt_formats(), "720p").merge_format is None
    with pytest.raises(AppError) as err:
        resolve_quality(yt_formats(), "1440p")
    assert err.value.code is ErrorCode.QUALITY_UNAVAILABLE
    assert "no longer available" in err.value.message


def test_no_formats_means_no_options():
    assert build_quality_options([]) == []


def test_orientation_aspect_and_short_classification():
    assert aspect_label(1080, 1920) == "9:16" and aspect_label(1920, 1080) == "16:9"
    assert aspect_label(1080, 1350) == "4:5" and aspect_label(1000, 700) == "10:7"
    assert orientation_of(1080, 1920) is Orientation.VERTICAL and orientation_of(1080, 1080) is Orientation.SQUARE
    assert classify(UrlKind.YOUTUBE_SHORT, Orientation.HORIZONTAL, 500) is ContentType.SHORT
    assert classify(UrlKind.YOUTUBE_VIDEO, Orientation.VERTICAL, 32) is ContentType.SHORT
    assert classify(UrlKind.YOUTUBE_VIDEO, Orientation.VERTICAL, 600) is ContentType.VIDEO
    assert classify(UrlKind.YOUTUBE_VIDEO, Orientation.HORIZONTAL, 222) is ContentType.VIDEO
