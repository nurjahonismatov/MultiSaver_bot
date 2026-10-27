import asyncio
import logging
import shutil
import uuid
from pathlib import Path
from typing import Optional

from config import get_settings

logger = logging.getLogger(__name__)


class FileManager:
    """Manage temporary download files with cleanup."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.temp_dir = self.settings.temp_path
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def generate_path(self, suffix: str = "", prefix: str = "ms_") -> Path:
        """Create a unique temporary file path."""
        name = f"{prefix}{uuid.uuid4().hex}{suffix}"
        return self.temp_dir / name

    def is_within_temp(self, path: Path) -> bool:
        """Ensure path is inside temp directory (path traversal protection)."""
        try:
            path.resolve().relative_to(self.temp_dir.resolve())
            return True
        except ValueError:
            return False

    async def cleanup(self, path: Optional[Path | str]) -> None:
        """Delete a single file safely."""
        if path is None:
            return
        p = Path(path)
        if not self.is_within_temp(p):
            logger.warning("Refusing to delete path outside temp: %s", p)
            return
        try:
            if p.exists() and p.is_file():
                p.unlink()
                logger.debug("Deleted temp file: %s", p)
        except OSError as exc:
            logger.warning("Failed to delete %s: %s", p, exc)

    async def cleanup_many(self, paths: list[Path | str]) -> None:
        for p in paths:
            await self.cleanup(p)

    async def cleanup_old(self, max_age_seconds: int = 3600) -> int:
        """Remove files older than max_age_seconds. Returns count deleted."""
        import time

        now = time.time()
        deleted = 0
        for f in self.temp_dir.iterdir():
            if f.is_file():
                try:
                    age = now - f.stat().st_mtime
                    if age > max_age_seconds:
                        f.unlink()
                        deleted += 1
                except OSError:
                    pass
        return deleted

    def get_size(self, path: Path | str) -> int:
        p = Path(path)
        if p.exists() and p.is_file():
            return p.stat().st_size
        return 0


# Singleton-style helper
_file_manager: Optional[FileManager] = None


def get_file_manager() -> FileManager:
    global _file_manager
    if _file_manager is None:
        _file_manager = FileManager()
    return _file_manager
