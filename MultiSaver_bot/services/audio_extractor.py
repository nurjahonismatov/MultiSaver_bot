import asyncio
import logging
from pathlib import Path

from services.file_manager import get_file_manager
from utils.errors import AudioExtractionError

logger = logging.getLogger(__name__)


async def extract_audio(video_path: Path | str, output_format: str = "mp3") -> Path:
    """
    Extract audio track from video using FFmpeg.
    Returns path to the resulting audio file.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise AudioExtractionError("Source video not found")

    fm = get_file_manager()
    out_path = fm.generate_path(suffix=f".{output_format}")

    # -vn: no video, -acodec libmp3lame for mp3, -q:a 2 good quality
    if output_format == "mp3":
        codec_args = ["-acodec", "libmp3lame", "-q:a", "2"]
    else:
        codec_args = ["-acodec", "copy"]

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        *codec_args,
        str(out_path),
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=90)

        if proc.returncode != 0:
            err_text = (stderr or b"").decode(errors="replace")[:500]
            logger.error("FFmpeg failed: %s", err_text)
            await fm.cleanup(out_path)
            raise AudioExtractionError("FFmpeg extraction failed")

        if not out_path.exists() or out_path.stat().st_size == 0:
            await fm.cleanup(out_path)
            raise AudioExtractionError("Empty audio output")

        return out_path

    except asyncio.TimeoutError:
        await fm.cleanup(out_path)
        raise AudioExtractionError("Audio extraction timed out")
    except FileNotFoundError:
        raise AudioExtractionError("FFmpeg is not installed")
