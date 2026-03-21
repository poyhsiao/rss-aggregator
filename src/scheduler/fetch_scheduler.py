"""Scheduler for periodic RSS fetching."""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.config import settings
from src.utils.time import now as get_now

logger = logging.getLogger(__name__)


class FetchScheduler:
    """Scheduler for periodic RSS feed fetching."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        check_interval: int = 60,
        max_concurrent: int = 5,
    ) -> None:
        self.session_factory = session_factory
        self.check_interval = check_interval
        self.max_concurrent = max_concurrent
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Fetch scheduler started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Fetch scheduler stopped")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                await self._check_and_fetch()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")

            await asyncio.sleep(self.check_interval)

    async def _check_and_fetch(self) -> None:
        from src.models import Source
        from src.services.fetch_service import FetchService

        async with self.session_factory() as session:
            fetch_service = FetchService(session)

            now = get_now()
            result = await session.execute(
                select(Source).where(
                    Source.is_active == True,  # noqa: E712
                    Source.deleted_at.is_(None),
                )
            )
            sources = list(result.scalars().all())

            sources_to_fetch = [
                s
                for s in sources
                if s.fetch_interval > 0
                and (
                    s.last_fetched_at is None
                    or (now - s.last_fetched_at).total_seconds() >= s.fetch_interval
                )
            ]

            if not sources_to_fetch:
                return

            semaphore = asyncio.Semaphore(self.max_concurrent)

            async def fetch_with_semaphore(source: Source) -> None:
                async with semaphore:
                    await fetch_service.fetch_source(source)

            tasks = [fetch_with_semaphore(s) for s in sources_to_fetch]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def refresh_source(self, source_id: int) -> None:
        from src.models import Source
        from src.services.fetch_service import FetchService

        async with self.session_factory() as session:
            fetch_service = FetchService(session)
            result = await session.execute(
                select(Source).where(Source.id == source_id)
            )
            source = result.scalar_one_or_none()
            if source:
                await fetch_service.fetch_source(source)

    async def refresh_all(self) -> None:
        from src.services.fetch_service import FetchService

        async with self.session_factory() as session:
            fetch_service = FetchService(session)
            await fetch_service.fetch_all()