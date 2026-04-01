"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "rss-aggregator"
    app_env: str = "development"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_timezone: str = "Asia/Taipei"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/rss.db"

    # API Key
    default_api_key: str = ""
    require_api_key: bool = True

    # Rate Limiting
    rate_limit_requests: int = 60
    rate_limit_window: int = 60

    # RSS Fetching
    fetch_timeout: int = 30
    fetch_retry_count: int = 3
    fetch_retry_delay: int = 5
    max_feed_items: int = 1000

    # Scheduler
    scheduler_enabled: bool = True
    scheduler_interval: int = 60

    # Default Sources
    default_sources: str = ""

    # CORS
    allowed_origins: str = ""

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def timezone(self) -> ZoneInfo:
        """Get the configured timezone as ZoneInfo object."""
        return ZoneInfo(self.app_timezone)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()