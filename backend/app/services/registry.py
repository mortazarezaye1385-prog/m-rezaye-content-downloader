from __future__ import annotations

from app.core.config import Settings
from app.security.tickets import TicketSigner
from app.security.url_validation import Platform
from app.services.base import PlatformService
from app.services.instagram.service import InstagramService
from app.services.tiktok.service import TikTokService
from app.services.youtube.service import YouTubeService
from app.services.ytdlp_client import YtDlpClient


class ServiceRegistry:
    def __init__(self, services: dict[Platform, PlatformService]) -> None:
        self._services = services

    @classmethod
    def default(cls, settings: Settings, signer: TicketSigner) -> "ServiceRegistry":
        engine = YtDlpClient(settings)
        return cls({
            Platform.INSTAGRAM: InstagramService(settings, signer, engine),
            Platform.TIKTOK: TikTokService(settings, signer, engine),
            Platform.YOUTUBE: YouTubeService(settings, signer, engine),
        })

    def get(self, platform: Platform) -> PlatformService:
        return self._services[platform]
