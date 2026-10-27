"""URL validation and SSRF protection."""

import ipaddress
import re
from urllib.parse import urlparse

from utils.errors import InvalidURLError

ALLOWED_SCHEMES = {"http", "https"}

PLATFORM_PATTERNS = {
    "youtube": re.compile(
        r"(?:https?://)?(?:(?:www|m|music)\.)?(?:youtube\.com|youtu\.be)/",
        re.IGNORECASE,
    ),
    "tiktok": re.compile(
        r"(?:https?://)?(?:(?:www|m|vm|vt)\.)?tiktok\.com/",
        re.IGNORECASE,
    ),
    "instagram": re.compile(
        r"(?:https?://)?(?:(?:www|m)\.)?(?:instagram\.com|instagr\.am)/",
        re.IGNORECASE,
    ),
    "likee": re.compile(
        r"(?:https?://)?(?:(?:www|m)\.)?(?:likee\.video|likeevideo\.com|l\.likee\.video)/",
        re.IGNORECASE,
    ),
    "telegram": re.compile(
        r"(?:https?://)?(?:t\.me|telegram\.me)/",
        re.IGNORECASE,
    ),
    "facebook": re.compile(
        r"(?:https?://)?(?:(?:www|m|web)\.)?(?:facebook\.com|fb\.watch|fb\.com)/",
        re.IGNORECASE,
    ),
    "pinterest": re.compile(
        r"(?:https?://)?(?:(?:www|pin)\.)?(?:pinterest\.[a-z.]+|pin\.it)/",
        re.IGNORECASE,
    ),
    "snapchat": re.compile(
        r"(?:https?://)?(?:(?:www|story|t)\.)?snapchat\.com/",
        re.IGNORECASE,
    ),
}

DOMAIN_MAP = (
    ("youtu.be", "youtube"),
    ("youtube.com", "youtube"),
    ("tiktok.com", "tiktok"),
    ("instagram.com", "instagram"),
    ("instagr.am", "instagram"),
    ("likee.video", "likee"),
    ("likeevideo.com", "likee"),
    ("t.me", "telegram"),
    ("telegram.me", "telegram"),
    ("facebook.com", "facebook"),
    ("fb.watch", "facebook"),
    ("fb.com", "facebook"),
    ("pinterest.", "pinterest"),
    ("pin.it", "pinterest"),
    ("t.snapchat.com", "snapchat"),
    ("snapchat.com", "snapchat"),
)


def is_private_ip(hostname: str) -> bool:
    try:
        ip = ipaddress.ip_address(hostname)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        )
    except ValueError:
        return False


def normalize_url(url: str) -> str:
    url = url.strip()
    if "://" in url:
        return url
    return "https://" + url


def validate_url(url: str) -> str:
    if not url or not isinstance(url, str):
        raise InvalidURLError("Empty URL")
    url = normalize_url(url)
    try:
        parsed = urlparse(url)
    except Exception as exc:
        raise InvalidURLError("Malformed URL") from exc
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise InvalidURLError("Only HTTP/HTTPS allowed")
    if not parsed.netloc:
        raise InvalidURLError("Missing host")
    hostname = parsed.hostname or ""
    if is_private_ip(hostname):
        raise InvalidURLError("Private addresses not allowed")
    if hostname.lower() in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
        raise InvalidURLError("Local addresses not allowed")
    if len(url) > 2048:
        raise InvalidURLError("URL too long")
    return url


def detect_platform(url: str):
    url = normalize_url(url)
    for platform, pattern in PLATFORM_PATTERNS.items():
        if pattern.search(url):
            return platform
    lower = url.lower()
    for domain, platform in DOMAIN_MAP:
        if domain in lower:
            return platform
    return None


def is_supported_url(url: str) -> bool:
    try:
        validate_url(url)
        return detect_platform(url) is not None
    except InvalidURLError:
        return False