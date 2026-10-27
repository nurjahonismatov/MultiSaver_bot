from pathlib import Path
from typing import Literal

MediaType = Literal["video", "image", "audio", "unknown"]

VIDEO_EXTS = {".mp4", ".webm", ".mkv", ".mov", ".avi", ".m4v", ".flv"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".flac"}


def detect_media_type(path: str | Path) -> MediaType:
    """Detect media type from file path extension."""
    ext = Path(path).suffix.lower()
    if ext in VIDEO_EXTS:
        return "video"
    if ext in IMAGE_EXTS:
        return "image"
    if ext in AUDIO_EXTS:
        return "audio"
    return "unknown"


def is_video(path: str | Path) -> bool:
    return detect_media_type(path) == "video"


def is_image(path: str | Path) -> bool:
    return detect_media_type(path) == "image"


def is_audio(path: str | Path) -> bool:
    return detect_media_type(path) == "audio"