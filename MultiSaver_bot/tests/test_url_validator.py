
import pytest

from services.url_validator import (
    detect_platform,
    is_supported_url,
    normalize_url,
    validate_url,
)
from utils.errors import InvalidURLError


def test_normalize_adds_scheme():
    assert normalize_url("instagram.com/p/abc").startswith("https://")


def test_valid_instagram():
    url = validate_url("https://www.instagram.com/reel/ABC123/")
    assert "instagram" in url
    assert detect_platform(url) == "instagram"


def test_valid_pinterest():
    url = validate_url("https://www.pinterest.com/pin/123456/")
    assert detect_platform(url) == "pinterest"


def test_valid_youtube():
    url = validate_url(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    assert detect_platform(url) == "youtube"


def test_private_ip_blocked():
    with pytest.raises(InvalidURLError):
        validate_url("http://127.0.0.1/secret")


def test_localhost_blocked():
    with pytest.raises(InvalidURLError):
        validate_url("http://localhost/admin")


def test_unsupported_scheme():
    with pytest.raises(InvalidURLError):
        validate_url("ftp://example.com/file")


def test_is_supported():
    assert is_supported_url("https://www.instagram.com/p/xyz/")
    assert is_supported_url(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    assert not is_supported_url("https://example.com/page")
