"""YouTube — kichik video Telegramga, katta uchun qisqa xabar."""

import asyncio
from pathlib import Path

from adapters.base import BaseAdapter, MediaResult
from config import get_settings
from services.ytdlp_helper import extract_direct_url, yt_dlp_download
from services.media_detector import detect_media_type
from utils.errors import NetworkError


class YouTubeAdapter(BaseAdapter):
    platform_name = "youtube"

    def can_handle(self, url: str) -> bool:
        u = url.lower()
        return "youtube.com" in u or "youtu.be" in u

    async def download(self, url: str, output_dir: Path) -> MediaResult:
        settings = get_settings()
        loop = asyncio.get_running_loop()
        fmt = "best[ext=mp4][height<=480]/best[height<=480]/best[ext=mp4]/best"

        media_url, title, filesize = await loop.run_in_executor(
            None, lambda: extract_direct_url(url, format_selector=fmt)
        )
        limit = min(settings.max_file_size_bytes, 45 * 1024 * 1024)
        should_download = filesize is None or filesize <= limit

        if should_download:
            try:
                files = await loop.run_in_executor(
                    None, lambda: yt_dlp_download(url, output_dir, format_selector=fmt)
                )
            except Exception:
                files = []

            if files:
                total = sum(f.stat().st_size for f in files if f.exists())
                if total <= limit:
                    return MediaResult(
                        files=files,
                        media_type=detect_media_type(files[0]),
                        title=title,
                        original_url=url,
                        platform=self.platform_name,
                        can_extract_audio=True,
                    )
                for f in files:
                    try:
                        f.unlink()
                    except OSError:
                        pass

        # Uzun CDN emas — oddiy YouTube link
        return MediaResult(
            files=[],
            media_type="link",
            title=title or "YouTube video",
            original_url=url,
            direct_url=url,
            platform=self.platform_name,
            can_extract_audio=False,
        )