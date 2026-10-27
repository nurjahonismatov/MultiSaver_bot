"""Pinterest adapter."""

import asyncio
from pathlib import Path

from adapters.base import BaseAdapter, MediaResult
from services.ytdlp_helper import extract_direct_url, yt_dlp_download
from services.media_detector import detect_media_type
from utils.errors import UnsupportedPlatformError


class PinterestAdapter(BaseAdapter):
    platform_name = "pinterest"

    def can_handle(self, url: str) -> bool:
        u = url.lower()
        return "pinterest." in u or "pin.it" in u

    async def download(self, url: str, output_dir: Path) -> MediaResult:
        loop = asyncio.get_running_loop()
        media_url, title, _ = await loop.run_in_executor(
            None, lambda: extract_direct_url(url, format_selector="best")
        )
        try:
            files = await loop.run_in_executor(
                None, lambda: yt_dlp_download(url, output_dir, format_selector="best")
            )
        except Exception:
            files = []

        if files:
            return MediaResult(
                files=files,
                media_type=detect_media_type(files[0]),
                title=title,
                original_url=url,
                platform=self.platform_name,
                can_extract_audio=False,
            )
        if media_url:
            short = media_url if len(media_url) < 400 else url
            return MediaResult(
                files=[],
                media_type="link",
                title=title or "Pinterest",
                original_url=url,
                direct_url=short,
                platform=self.platform_name,
                can_extract_audio=False,
            )
        raise UnsupportedPlatformError("Pinterest media olinmadi")