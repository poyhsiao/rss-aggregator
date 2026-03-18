"""Scheduler for periodic RSS fetching."""

import asyncio
import logging
from typing import TYPE_CHECKING

from src.config import settings

if TYPE_CHECKING:
    from src.services.fetch_service import FetchService

logger = logging.getLogger(__name__)


class FetchScheduler:
    """Scheduler for periodic RSS feed fetching."""

    def __init__(
        self,
        fetch_service: "FetchService",
        check_interval: int = 60,
        max_concurrent: int = 5,
    ) -> None:
        """Initialize scheduler.

        Args:
            fetch_service: Service for fetching feeds.
            check_interval: Seconds between checks.
            max_concurrent: Maximum concurrent fetches.
        """
        self.fetch_service = fetch_service
        self.check_interval = check_interval
        self.max_concurrent = max_concurrent
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Fetch scheduler started")

    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Fetch scheduler stopped")

    async def _run_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_and_fetch()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")

            await asyncio.sleep(self.check_interval)

    async def _check_and_fetch(self) -> None:
        """Check sources and fetch those that need updating."""
        from datetime import datetime, timedelta

        from sqlalchemy import select

        from src.models import Source

        # Get sources that need fetching
        now = datetime.utcnow()
        result = await self.fetch_service.session.execute(
            select(Source).where(
                Source.is_active == True,  # noqa: E712
                Source.deleted_at.is_(None),
            )
        )
        sources = list(result.scalars().all())

        sources_to_fetch = [
            s
            for s in sources
            if s.last_fetched_at is None
            or (now - s.last_fetched_at).total_seconds() >= s.fetch_interval
        ]

        if not sources_to_fetch:
            return

        # Fetch with concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def fetch_with_semaphore(source: Source) -> None:
            async with semaphore:
                await self.fetch_service.fetch_source(source)

        tasks = [fetch_with_semaphore(s) for s in sources_to_fetch]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def refresh_source(self, source_id: int) -> None:
        """Manually refresh a specific source.

        Args:
            source_id: Source ID to refresh.
        """
        source = await self.fetch_service.get_source(source_id)
        if source:
            await self.fetch_service.fetch_source(source)

    async def refresh_all(self) -> None:
        """Manually refresh all active sources."""
        await self.fetch_service.fetch_all()