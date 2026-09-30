import asyncio

import pytest

from app.core.errors import AppError, ErrorCode
from app.schemas.media import ContentType, MediaKind, SourceCondition
from app.security.tickets import TicketSigner
from app.security.url_validation import parse_supported_url
from app.services.base import TICKET_DOWNLOAD, ProviderSkip
from app.services.engine_normalize import TIKTOK_SELECTOR, tiktok_source_condition
from app.services.instagram.providers import graph_node_to_item, shortcode_matches
from app.services.instagram.service import InstagramService
from app.services.tiktok.service import TikTokService
from app.services.youtube.service import YouTubeService
from tests.fakes import FakeEngine, make_settings, yt_formats

SETTINGS = make_settings()
SIGNER = TicketSigner(SETTINGS.secret_key)


def run(coro):
    return asyncio.run(coro)


def video_entry(h=1920, w=1080, note=""):
    return {"title": "clip", "duration": 12.5, "ext": "mp4", "thumbnail": "https://p16.tiktokcdn.com/t.jpg",
            "formats": [{"format_id": "a", "ext": "mp4", "vcodec": "h264", "acodec": "aac", "height": h, "width": w, "format_note": note, "filesize": 900}]}


def test_youtube_analysis_lists_real_qualities_and_orientation():
    info = {"title": "Talk", "channel": "Chan", "duration": 222, "formats": yt_formats(), "thumbnails": [{"url": "https://i.ytimg.com/a.jpg", "width": 1280, "height": 720}]}
    service = YouTubeService(SETTINGS, SIGNER, FakeEngine(info))
    result = run(service.analyze(parse_supported_url("https://youtu.be/dQw4w9WgXcQ")))
    assert result.content_type is ContentType.VIDEO and result.aspect_ratio == "16:9"
    assert [q.id for q in result.qualities] == ["2160p", "1080p60", "1080p", "720p"]
    assert result.items[0].preview_url.startswith("/api/preview?t=")


def test_youtube_plan_rechecks_quality():
    info = {"title": "Talk", "formats": yt_formats()}
    service = YouTubeService(SETTINGS, SIGNER, FakeEngine(info))
    ticket = {"u": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "t": "Talk"}
    plan = run(service.plan_download(ticket, "1080p"))
    assert plan.steps[0].format_selector == "137+140" and plan.steps[0].merge_format == "mp4"
    with pytest.raises(AppError) as err:
        run(service.plan_download(ticket, "4320p"))
    assert err.value.code is ErrorCode.QUALITY_UNAVAILABLE


def test_youtube_live_is_rejected():
    service = YouTubeService(SETTINGS, SIGNER, FakeEngine({"is_live": True, "formats": yt_formats()}))
    with pytest.raises(AppError) as err:
        run(service.analyze(parse_supported_url("https://youtu.be/dQw4w9WgXcQ")))
    assert err.value.code is ErrorCode.UNSUPPORTED_CONTENT_TYPE


def test_instagram_carousel_gets_items_and_bundle():
    info = {"_type": "playlist", "title": "post", "entries": [video_entry(), None, video_entry(1350, 1080)]}
    service = InstagramService(SETTINGS, SIGNER, FakeEngine(info))
    result = run(service.analyze(parse_supported_url("https://www.instagram.com/p/C1a2B3c4D5e/")))
    assert result.content_type is ContentType.CAROUSEL and len(result.items) == 2
    assert result.bundle_ticket and any("weren't exposed" in n for n in result.notices)
    bundle = SIGNER.verify(result.bundle_ticket, purpose=TICKET_DOWNLOAD)
    plan = run(service.plan_download(bundle, None))
    assert plan.bundle and [s.playlist_index for s in plan.steps] == [1, 3]


def test_instagram_photo_only_post_is_explained_not_faked():
    service = InstagramService(SETTINGS, SIGNER, FakeEngine(error=AppError(ErrorCode.UNSUPPORTED_BY_PROVIDER)))
    with pytest.raises(AppError) as err:
        run(service.analyze(parse_supported_url("https://www.instagram.com/p/C1a2B3c4D5e/")))
    assert err.value.code is ErrorCode.UNSUPPORTED_BY_PROVIDER


def test_highlight_states():
    url = parse_supported_url("https://www.instagram.com/stories/highlights/17912345678901234/")
    login = InstagramService(SETTINGS, SIGNER, FakeEngine(error=AppError(ErrorCode.LOGIN_REQUIRED)))
    with pytest.raises(AppError) as unsupported:
        run(login.analyze_highlight(url))
    assert unsupported.value.code is ErrorCode.UNSUPPORTED_BY_PROVIDER and "never signs in" in unsupported.value.message
    private = InstagramService(SETTINGS, SIGNER, FakeEngine(error=AppError(ErrorCode.PRIVATE_CONTENT)))
    with pytest.raises(AppError) as priv:
        run(private.analyze_highlight(url))
    assert priv.value.code is ErrorCode.PRIVATE_CONTENT
    ok = InstagramService(SETTINGS, SIGNER, FakeEngine({"_type": "playlist", "entries": [video_entry(), video_entry()]}))
    assert run(ok.analyze_highlight(url)).content_type is ContentType.HIGHLIGHT
    with pytest.raises(AppError) as wrong:
        run(ok.analyze_highlight(parse_supported_url("https://www.instagram.com/p/C1a2B3c4D5e/")))
    assert wrong.value.code is ErrorCode.INVALID_URL


def test_provider_chain_falls_through_skip_but_not_private():
    class Skip:
        name = "skip"

        async def fetch(self, parsed):
            raise ProviderSkip()

    class Private:
        name = "private"

        async def fetch(self, parsed):
            raise AppError(ErrorCode.PRIVATE_CONTENT)

    engine = FakeEngine({"_type": "playlist", "entries": [video_entry()]})
    from app.services.instagram.providers import InstagramEngineProvider
    svc = InstagramService(SETTINGS, SIGNER, engine, providers=[Skip(), InstagramEngineProvider(SETTINGS, engine)])
    assert run(svc.analyze(parse_supported_url("https://www.instagram.com/reel/C9zYxWvUtS1/"))).items
    svc2 = InstagramService(SETTINGS, SIGNER, engine, providers=[Private(), InstagramEngineProvider(SETTINGS, engine)])
    with pytest.raises(AppError) as err:
        run(svc2.analyze(parse_supported_url("https://www.instagram.com/reel/C9zYxWvUtS1/")))
    assert err.value.code is ErrorCode.PRIVATE_CONTENT


def test_graph_helpers():
    assert shortcode_matches("https://www.instagram.com/p/ABC123/", "ABC123")
    assert not shortcode_matches("https://www.instagram.com/p/ABC1234/", "ABC123")
    img = graph_node_to_item({"media_type": "IMAGE", "media_url": "https://scontent.cdninstagram.com/x/photo.jpg?a=1"})
    assert img.kind is MediaKind.IMAGE and img.ext == "jpg" and img.direct_url
    assert graph_node_to_item({"media_type": "VIDEO"}) is None


def test_tiktok_watermark_is_reported_honestly():
    assert tiktok_source_condition(video_entry(note="Download video, watermarked")["formats"]) is SourceCondition.WATERMARKED
    assert tiktok_source_condition(video_entry(note="Direct video")["formats"]) is SourceCondition.UNKNOWN
    service = TikTokService(SETTINGS, SIGNER, FakeEngine(video_entry()))
    result = run(service.analyze(parse_supported_url("https://www.tiktok.com/@a.b/video/7301234567890123456")))
    assert result.content_type is ContentType.VIDEO and result.aspect_ratio == "9:16"
    payload = SIGNER.verify(result.items[0].ticket, purpose=TICKET_DOWNLOAD)
    assert payload["fs"] == TIKTOK_SELECTOR


def test_tiktok_caption_prefers_oembed_then_engine():
    class OEmbed:
        name = "oembed"

        async def caption(self, parsed):
            return "hello #fyp", "author"

    class Down:
        name = "down"

        async def caption(self, parsed):
            raise ProviderSkip()

    engine = FakeEngine({"description": "from engine", "uploader": "u"})
    from app.services.tiktok.providers import TikTokEngineProvider
    parsed = parse_supported_url("https://www.tiktok.com/@a.b/video/7301234567890123456")
    assert run(TikTokService(SETTINGS, SIGNER, engine, caption_providers=[OEmbed()]).caption(parsed)).caption == "hello #fyp"
    fallback = TikTokService(SETTINGS, SIGNER, engine, caption_providers=[Down(), TikTokEngineProvider(SETTINGS, engine)])
    assert run(fallback.caption(parsed)).caption == "from engine"
    empty = TikTokService(SETTINGS, SIGNER, FakeEngine({}), caption_providers=[TikTokEngineProvider(SETTINGS, FakeEngine({}))])
    assert run(empty.caption(parsed)).caption is None
