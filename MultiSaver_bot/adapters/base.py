"""Base adapter interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class MediaResult:
    files: List[Path] = field(default_factory=list)
    media_type: str = "unknown"  # video, image, audio, carousel, link
    title: Optional[str] = None
    original_url: Optional[str] = None
    direct_url: Optional[str] = None  # katta video uchun to'g'ridan-to'g'ri havola
    platform: str = "unknown"
    can_extract_audio: bool = False


class BaseAdapter(ABC):
    platform_name: str = "unknown"

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        ...

    @abstractmethod
    async def download(self, url: str, output_dir: Path) -> MediaResult:
        ...