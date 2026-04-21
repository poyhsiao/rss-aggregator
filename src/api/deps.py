"""Dependency injection for FastAPI."""

from typing import AsyncGenerator, Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.database import get_session
from src.scheduler.fetch_scheduler import FetchScheduler
from src.models.app_settings import AppSettings
from src.services.auth_service import AuthService
from src.services.feed_service import FeedService
from src.services.fetch_service import FetchService
from src.services.history_service import HistoryService
from src.services.preview_service import PreviewService
from src.services.rate_limiter import RateLimiter
from src.services.source_service import SourceService
from src.services.backup_service import BackupService
from src.services.source_group_service import SourceGroupService
from src.services.source_group_schedule_service import SourceGroupScheduleService


_rate_limiter: RateLimiter | None = None
_scheduler: FetchScheduler | None = None


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            max_requests=settings.rate_limit_requests,
            window_seconds=settings.rate_limit_window,
        )
    return _rate_limiter


def get_scheduler() -> FetchScheduler:
    """Get scheduler instance."""
    if _scheduler is None:
        raise RuntimeError("Scheduler not initialized")
    return _scheduler


def set_scheduler(scheduler: FetchScheduler) -> None:
    """Set scheduler instance."""
    global _scheduler
    _scheduler = scheduler


async def get_auth_service(
    session: AsyncSession = Depends(get_session),
) -> AuthService:
    """Get AuthService instance."""
    return AuthService(session)


async def get_source_service(
    session: AsyncSession = Depends(get_session),
) -> SourceService:
    """Get SourceService instance."""
    return SourceService(session)


async def get_feed_service(
    session: AsyncSession = Depends(get_session),
) -> FeedService:
    """Get FeedService instance."""
    return FeedService(session)


async def get_fetch_service(
    session: AsyncSession = Depends(get_session),
) -> FetchService:
    """Get FetchService instance."""
    return FetchService(session)


async def get_history_service(
    session: AsyncSession = Depends(get_session),
) -> HistoryService:
    """Get HistoryService instance."""
    return HistoryService(session)


async def get_preview_service(
    session: AsyncSession = Depends(get_session),
) -> PreviewService:
    """Get PreviewService instance."""
    return PreviewService(session)


async def get_backup_service(
    session: AsyncSession = Depends(get_session),
) -> BackupService:
    return BackupService(session)


async def get_source_group_service(
    session: AsyncSession = Depends(get_session),
) -> SourceGroupService:
    return SourceGroupService(session)


async def get_schedule_service(
    session: AsyncSession = Depends(get_session),
) -> SourceGroupScheduleService:
    return SourceGroupScheduleService(session)


async def get_app_settings(session: AsyncSession = Depends(get_session)) -> AppSettings:
    """Return the singleton AppSettings record, creating it if absent."""
    result = await session.execute(select(AppSettings))
    settings = result.scalars().first()
    if settings is None:
        settings = AppSettings()
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
    return settings


async def require_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    auth_service: AuthService = Depends(get_auth_service),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> Optional[str]:
    """Validate API key and check rate limit.

    If REQUIRE_API_KEY is set to false in environment, skips validation.

    Args:
        x_api_key: API key from header (optional if REQUIRE_API_KEY=false).
        auth_service: Auth service instance.
        rate_limiter: Rate limiter instance.

    Returns:
        Validated API key or None if validation is disabled.

    Raises:
        HTTPException: If key is invalid or rate limited.
    """
    # Skip validation if REQUIRE_API_KEY is false
    if not settings.require_api_key:
        return None

    # API key is required when validation is enabled
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required",
        )

    if not rate_limiter.is_allowed(x_api_key):
        reset_time = rate_limiter.get_reset_time(x_api_key)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(rate_limiter.max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(reset_time)),
                "Retry-After": str(int(reset_time)),
            },
        )

    if not await auth_service.validate_key(x_api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    return x_api_key