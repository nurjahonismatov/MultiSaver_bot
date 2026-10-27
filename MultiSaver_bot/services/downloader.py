"""Core downloader."""

import asyncio
import logging
from pathlib import Path

from adapters.base import MediaResult
from adapters.facebook import FacebookAdapter
from adapters.instagram import InstagramAdapter
from adapters.likee import LikeeAdapter
from adapters.pinterest import PinterestAdapter
from adapters.snapchat import SnapchatAdapter
from adapters.telegram_media import TelegramMediaAdapter
from adapters.tiktok import TikTokAdapter
from adapters.youtube import YouTubeAdapter
from config import get_settings
from services.file_manager import get_file_manager
from services.media_detector import detect_media_type
from services.url_validator import detect_platform, validate_url
from utils.errors import (
    DownloadTimeoutError,
    FileTooLargeError,
    NetworkError,
    UnsupportedPlatformError,
)

logger = logging.getLogger(__name__)

ADAPTERS = [
    YouTubeAdapter(),
    TikTokAdapter(),
    InstagramAdapter(),
    LikeeAdapter(),
    TelegramMediaAdapter(),
    FacebookAdapter(),
    PinterestAdapter(),
    SnapchatAdapter(),
]


def _get_adapter(url: str):
    for adapter in ADAPTERS:
        if adapter.can_handle(url):
            return adapter
    return None


async def download_media(url: str) -> MediaResult:
    settings = get_settings()
    fm = get_file_manager()

    url = validate_url(url)
    platform = detect_platform(url)
    if platform is None:
        raise UnsupportedPlatformError()

    adapter = _get_adapter(url)
    if adapter is None:
        raise UnsupportedPlatformError()

    job_dir = fm.generate_path(prefix="job_", suffix="")
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = await asyncio.wait_for(
            adapter.download(url, job_dir),
            timeout=settings.max_download_time_seconds,
        )
    except asyncio.TimeoutError:
        await _cleanup_dir(job_dir)
        raise DownloadTimeoutError()
    except Exception:
        await _cleanup_dir(job_dir)
        raise

    if getattr(result, "media_type", None) == "link" and getattr(result, "direct_url", None):
        result.platform = platform
        if not result.original_url:
            result.original_url = url
        return result

    valid_files = []
    for f in result.files:
        size = fm.get_size(f)
        if size > settings.max_file_size_bytes:
            await fm.cleanup(f)
            raise FileTooLargeError()
        if size > 0:
            valid_files.append(f)

    if not valid_files:
        await _cleanup_dir(job_dir)
        raise NetworkError("No media retrieved")

    result.files = valid_files
    if result.media_type == "unknown" and valid_files:
        result.media_type = detect_media_type(valid_files[0])
    result.platform = platform
    result.original_url = url
    return result


async def _cleanup_dir(directory: Path) -> None:
    fm = get_file_manager()
    if directory.exists() and directory.is_dir():
        for f in directory.iterdir():
            await fm.cleanup(f)
        try:
            directory.rmdir()
        except OSError:
            pass