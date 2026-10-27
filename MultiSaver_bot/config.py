from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
    env_file=Path(__file__).resolve().parent / ".env",
    env_file_encoding="utf-8",
    case_sensitive=False,
    extra="ignore",
)

    bot_token: str = Field(default="TEST_TOKEN_REPLACE_ME", description="Telegram Bot Token from BotFather")
    admin_ids: str = Field(default="", description="Comma-separated Telegram admin user IDs")
    database_url: str = Field(
        default="sqlite+aiosqlite:///./multisaver.db",
        description="SQLAlchemy database URL",
    )
    max_file_size_mb: int = Field(default=45, ge=1, le=50)
    max_concurrent_downloads: int = Field(default=3, ge=1, le=10)
    max_download_time_seconds: int = Field(default=120, ge=30, le=300)
    log_level: str = Field(default="INFO")
    rate_limit_requests: int = Field(default=10, ge=1)
    rate_limit_period: int = Field(default=60, ge=10)
    temp_dir: str = Field(default="./temp")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: str | List[int] | None) -> str:
        if v is None:
            return ""
        if isinstance(v, list):
            return ",".join(str(i) for i in v)
        return str(v)

    @property
    def admin_id_list(self) -> List[int]:
        """Return list of admin user IDs."""
        if not self.admin_ids.strip():
            return []
        result = []
        for part in self.admin_ids.split(","):
            part = part.strip()
            if part.isdigit():
                result.append(int(part))
        return result

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def temp_path(self) -> Path:
        path = Path(self.temp_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()

cookies_from_browser: str = Field(default="")