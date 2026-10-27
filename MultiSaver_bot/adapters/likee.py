"""Likee adapter."""

import asyncio
from pathlib import Path

from adapters.base import BaseAdapter, MediaResult
from services.ytdlp_helper import yt_dlp_download
from services.media_detector import detect_media_type
from utils.errors import UnsupportedPlatformError


class LikeeAdapter(BaseAdapter):
    platform_name = "likee"

    def can_handle(self, url: str) -> bool:
        u = url.lower()
        return "likee.video" in u or "likeevideo.com" in u

    async def download(self, url: str, output_dir: Path) -> MediaResult:
        loop = asyncio.get_running_loop()
        try:
            files = await loop.run_in_executor(
                None,
                lambda: yt_dlp_download(url, output_dir, format_selector="best"),
            )
        except Exception:
            raise UnsupportedPlatformError("Likee yuklanmadi")
        if not files:
            raise UnsupportedPlatformError("Likee media yo'q")
        return MediaResult(
            files=files,
            media_type=detect_media_type(files[0]),
            platform=self.platform_name,
            can_extract_audio=True,
            original_url=url,
        )