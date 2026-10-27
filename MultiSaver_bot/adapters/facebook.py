import asyncio
from pathlib import Path

from adapters.base import BaseAdapter, MediaResult
from services.ytdlp_helper import yt_dlp_download
from services.media_detector import detect_media_type
from services.url_validator import PLATFORM_PATTERNS
from utils.errors import UnsupportedPlatformError


class FacebookAdapter(BaseAdapter):
    platform_name = "facebook"

    def can_handle(self, url: str) -> bool:
        return bool(PLATFORM_PATTERNS["facebook"].search(url))

    async def download(self, url: str, output_dir: Path) -> MediaResult:
        loop = asyncio.get_running_loop()
        files = await loop.run_in_executor(
            None,
            lambda: yt_dlp_download(
                url,
                output_dir,
                format_selector="bestvideo[ext=mp4]+bestaudio/best[ext=mp4]/best",
            ),
        )

        if not files:
            raise UnsupportedPlatformError(
                "Facebook media could not be retrieved. Only some public videos are supported."
            )

        media_type = detect_media_type(files[0])
        return MediaResult(
            files=files,
            media_type=media_type,
            platform=self.platform_name,
            can_extract_audio=(media_type == "video"),
            original_url=url,
        )

