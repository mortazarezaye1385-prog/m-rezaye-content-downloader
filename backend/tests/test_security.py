import pytest

from app.core.errors import AppError, ErrorCode
from app.security.rate_limit import TokenBucketLimiter
from app.security.ssrf import host_matches_suffix, is_public_ip, validate_outbound_url
from app.security.tickets import TicketSigner


class Clock:
    def __init__(self, now: float = 1000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


@pytest.mark.parametrize("ip, public", [
    ("8.8.8.8", True), ("127.0.0.1", False), ("10.1.2.3", False), ("192.168.1.1", False),
    ("169.254.169.254", False), ("::1", False), ("::ffff:127.0.0.1", False), ("0.0.0.0", False), ("fd00::1", False),
    ("2607:f8b0:4005:80a::200e", True), ("not-an-ip", False),
])
def test_is_public_ip(ip, public):
    assert is_public_ip(ip) is public


def test_host_suffix_matching_is_strict():
    assert host_matches_suffix("scontent.cdninstagram.com")
    assert host_matches_suffix("rr1---sn-abc.googlevideo.com")
    assert not host_matches_suffix("cdninstagram.com.evil.example")
    assert not host_matches_suffix("evilcdninstagram.com")


def test_outbound_validation():
    public = lambda _h: ["93.184.216.34"]  # noqa: E731
    private = lambda _h: ["10.0.0.5"]  # noqa: E731
    assert validate_outbound_url("https://scontent.cdninstagram.com/v/a.jpg", resolver=public)
    for bad in ["http://scontent.cdninstagram.com/a.jpg", "https://example.com/a.jpg", "https://user@scontent.cdninstagram.com/a", "https://scontent.cdninstagram.com:8443/a"]:
        with pytest.raises(AppError):
            validate_outbound_url(bad, resolver=public)
    with pytest.raises(AppError):
        validate_outbound_url("https://scontent.cdninstagram.com/a.jpg", resolver=private)
    with pytest.raises(AppError):
        validate_outbound_url("https://graph.instagram.com/v21.0/me", resolver=public)
    assert validate_outbound_url("https://graph.instagram.com/v21.0/me", allow_api_hosts=True, resolver=public)


def test_tickets_roundtrip_tamper_and_expiry():
    clock = Clock()
    signer = TicketSigner("x" * 32, clock=clock)
    token = signer.sign({"u": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}, purpose="download", ttl_seconds=60)
    assert signer.verify(token, purpose="download")["u"].endswith("dQw4w9WgXcQ")
    with pytest.raises(AppError) as wrong_purpose:
        signer.verify(token, purpose="preview")
    assert wrong_purpose.value.code is ErrorCode.INVALID_TICKET
    body, sig = token.split(".")
    with pytest.raises(AppError):
        signer.verify(body[:-2] + "AA." + sig, purpose="download")
    with pytest.raises(AppError):
        TicketSigner("y" * 32, clock=clock).verify(token, purpose="download")
    clock.now += 61
    with pytest.raises(AppError) as expired:
        signer.verify(token, purpose="download")
    assert expired.value.code is ErrorCode.TICKET_EXPIRED


def test_rate_limiter_refills():
    clock = Clock()
    limiter = TokenBucketLimiter(per_minute=2, clock=clock)
    assert limiter.check("a")[0]
    assert limiter.check("a")[0]
    allowed, retry = limiter.check("a")
    assert not allowed and retry > 0
    assert limiter.check("b")[0]  # independent keys
    clock.now += 30
    assert limiter.check("a")[0]
