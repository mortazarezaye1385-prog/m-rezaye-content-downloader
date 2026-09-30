"""HTTP-level tests with a fake retrieval engine (requires fastapi + httpx)."""

import time

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import build_state, create_app  # noqa: E402
from app.security.tickets import TicketSigner  # noqa: E402
from app.security.url_validation import Platform  # noqa: E402
from app.services.instagram.service import InstagramService  # noqa: E402
from app.services.registry import ServiceRegistry  # noqa: E402
from app.services.tiktok.service import TikTokService  # noqa: E402
from app.services.youtube.service import YouTubeService  # noqa: E402
from tests.fakes import FakeEngine, make_settings, yt_formats  # noqa: E402


@pytest.fixture()
def client(tmp_path):
    settings = make_settings(tmp_path, rate_limit_analyze_per_minute=5)
    engine = FakeEngine({"title": "Talk", "duration": 222, "formats": yt_formats()})
    signer = TicketSigner(settings.secret_key)
    registry = ServiceRegistry({
        Platform.YOUTUBE: YouTubeService(settings, signer, engine),
        Platform.INSTAGRAM: InstagramService(settings, signer, engine),
        Platform.TIKTOK: TikTokService(settings, signer, engine),
    })
    state = build_state(settings, services=registry, engine=engine)
    state.signer = signer
    with TestClient(create_app(settings, state)) as c:
        yield c


def test_health_and_security_headers(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.headers["x-content-type-options"] == "nosniff" and r.headers["x-request-id"]


def test_validation_errors_are_structured(client):
    r = client.post("/api/youtube/analyze", json={"url": "https://vimeo.com/1"})
    body = r.json()["error"]
    assert r.status_code == 422 and body["code"] == "unsupported_platform" and body["request_id"]
    assert client.post("/api/youtube/analyze", json={}).json()["error"]["code"] == "validation_error"
    assert client.post("/api/youtube/analyze", content=b"x" * 70000, headers={"content-type": "application/json"}).status_code == 413


def test_full_download_flow_deletes_file(client):
    analysis = client.post("/api/youtube/analyze", json={"url": "https://youtu.be/dQw4w9WgXcQ"}).json()
    assert [q["id"] for q in analysis["qualities"]][0] == "2160p"
    bad = client.post("/api/downloads", json={"ticket": analysis["items"][0]["ticket"], "quality_id": "4320p"})
    assert bad.status_code == 409 and bad.json()["error"]["code"] == "quality_unavailable"
    job = client.post("/api/downloads", json={"ticket": analysis["items"][0]["ticket"], "quality_id": "1080p"}).json()
    for _ in range(50):
        status = client.get(f"/api/downloads/{job['id']}").json()
        if status["status"] == "ready":
            break
        time.sleep(0.05)
    assert status["status"] == "ready" and status["progress"]["percent"] == 100.0
    file = client.get(f"/api/downloads/{job['id']}/file")
    assert file.status_code == 200 and "attachment" in file.headers["content-disposition"]
    assert client.get(f"/api/downloads/{job['id']}").json()["status"] == "completed"
    assert client.get(f"/api/downloads/{job['id']}/file").status_code == 404  # one-time


def test_forged_ticket_rejected(client):
    r = client.post("/api/downloads", json={"ticket": "abc.def-forged-ticket", "quality_id": "1080p"})
    assert r.status_code == 400 and r.json()["error"]["code"] == "invalid_ticket"


def test_rate_limit(client):
    codes = [client.post("/api/tiktok/caption", json={"url": "bad"}).status_code for _ in range(7)]
    assert 429 in codes
