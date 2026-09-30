"""Analysis and caption endpoints, one set per platform."""

from fastapi import APIRouter, Depends

from app.api.deps import get_state
from app.api.state import AppState
from app.schemas.media import CaptionResult, MediaAnalysis, UrlRequest
from app.security.url_validation import Platform, parse_supported_url
from app.services.instagram.service import InstagramService

router = APIRouter(prefix="/api", tags=["media"])


def _platform_routes(platform: Platform) -> None:
    @router.post(f"/{platform.value}/analyze", response_model=MediaAnalysis, name=f"{platform.value}_analyze")
    async def analyze(body: UrlRequest, state: AppState = Depends(get_state)) -> MediaAnalysis:
        parsed = parse_supported_url(body.url, expected=platform)
        return await state.services.get(platform).analyze(parsed)

    @router.post(f"/{platform.value}/caption", response_model=CaptionResult, name=f"{platform.value}_caption")
    async def caption(body: UrlRequest, state: AppState = Depends(get_state)) -> CaptionResult:
        parsed = parse_supported_url(body.url, expected=platform)
        return await state.services.get(platform).caption(parsed)


for _platform in Platform:
    _platform_routes(_platform)


@router.post("/instagram/highlight", response_model=MediaAnalysis)
async def instagram_highlight(body: UrlRequest, state: AppState = Depends(get_state)) -> MediaAnalysis:
    parsed = parse_supported_url(body.url, expected=Platform.INSTAGRAM)
    service = state.services.get(Platform.INSTAGRAM)
    assert isinstance(service, InstagramService)
    return await service.analyze_highlight(parsed)
