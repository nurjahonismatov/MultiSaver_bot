import asyncio
from pathlib import Path

from adapters.base import BaseAdapter, MediaResult
from services.ytdlp_helper import yt_dlp_download
from services.media_detector import detect_media_type
from services.url_validator import PLATFORM_PATTERNS
from utils.errors import UnsupportedPlatformError


class InstagramAdapter(BaseAdapter):
    platform_name = "instagram"

    def can_handle(self, url: str) -> bool:
        return bool(PLATFORM_PATTERNS["instagram"].search(url))

    async def download(self, url: str, output_dir: Path) -> MediaResult:
        loop = asyncio.get_running_loop()
        # Prefer mp4 video or best image
        files = await loop.run_in_executor(
            None,
            lambda: yt_dlp_download(
                url,
                output_dir,
                format_selector="bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            ),
        )

        if not files:
            raise UnsupportedPlatformError("No Instagram media retrieved")

        media_type = detect_media_type(files[0])
        can_audio = media_type == "video"

        return MediaResult(
            files=files,
            media_type=media_type if len(files) == 1 else "carousel",
            platform=self.platform_name,
            can_extract_audio=can_audio,
            original_url=url,
        )

