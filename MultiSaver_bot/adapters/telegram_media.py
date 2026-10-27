import asyncio
from pathlib import Path

from adapters.base import BaseAdapter, MediaResult
from services.ytdlp_helper import yt_dlp_download
from services.media_detector import detect_media_type
from services.url_validator import PLATFORM_PATTERNS
from utils.errors import UnsupportedPlatformError


class TelegramMediaAdapter(BaseAdapter):
    platform_name = "telegram"

    def can_handle(self, url: str) -> bool:
        return bool(PLATFORM_PATTERNS["telegram"].search(url))

    async def download(self, url: str, output_dir: Path) -> MediaResult:
        """
        yt-dlp has limited support for public Telegram posts.
        Private channels and most media require special access and are not supported.
        """
        loop = asyncio.get_running_loop()
        try:
            files = await loop.run_in_executor(
                None,
                lambda: yt_dlp_download(url, output_dir, format_selector="best"),
            )
        except Exception:
            raise UnsupportedPlatformError(
                "Telegram media download is limited to certain public posts"
            )

        if not files:
            raise UnsupportedPlatformError(
                "Could not retrieve Telegram media. Only some public posts are supported."
            )

        media_type = detect_media_type(files[0])
        return MediaResult(
            files=files,
            media_type=media_type,
            platform=self.platform_name,
            can_extract_audio=(media_type == "video"),
            original_url=url,
        )

