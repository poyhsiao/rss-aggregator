"""Scheduler for periodic RSS fetching."""

import asyncio
import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.config import settings
from src.utils.time import now as get_now

logger = logging.getLogger(__name__)


class FetchScheduler:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        check_interval: int = 60,
        max_concurrent: int = 5,
    ) -> None:
        self.session_factory = session_factory
        self.check_interval = check_interval
        self.max_concurrent = max_concurrent

    async def start(self) -> None:
        logger.info("Fetch scheduler initialized (triggered by ScheduleScheduler or manual calls)")

    async def stop(self) -> None:
        logger.info("Fetch scheduler stopped")

    async def _check_and_fetch(self) -> None:
        import json
        from src.models import FetchBatch, Source, SourceGroup, SourceGroupMember, SourceGroupSchedule
        from src.services.fetch_service import FetchService

        async with self.session_factory() as session:
            fetch_service = FetchService(session)

            # Only fetch sources that belong to groups with an enabled schedule
            scheduled_group_result = await session.execute(
                select(SourceGroupSchedule.group_id).where(
                    SourceGroupSchedule.is_enabled == True,  # noqa: E712
                )
            )
            scheduled_group_ids = list(scheduled_group_result.scalars().all())

            if not scheduled_group_ids:
                return

            result = await session.execute(
                select(Source)
                .join(SourceGroupMember, SourceGroupMember.source_id == Source.id)
                .where(
                    SourceGroupMember.group_id.in_(scheduled_group_ids),
                    Source.is_active == True,  # noqa: E712
                    Source.deleted_at.is_(None),
                )
                .distinct()
            )
            sources = list(result.scalars().all())

            sources_to_fetch = list(sources)

            if not sources_to_fetch:
                return

            group_result = await session.execute(
                select(SourceGroup)
                .join(SourceGroupMember, SourceGroup.id == SourceGroupMember.group_id)
                .where(SourceGroupMember.source_id.in_([s.id for s in sources_to_fetch]))
                .distinct()
            )
            groups = [{"id": g.id, "name": g.name} for g in group_result.scalars().all()]

            batch = FetchBatch(items_count=0, sources="", groups=json.dumps(groups, ensure_ascii=False))
            session.add(batch)
            await session.flush()

            semaphore = asyncio.Semaphore(self.max_concurrent)
            source_names: list[str] = []
            total_items = 0

            async def fetch_with_semaphore(source: Source) -> int:
                async with semaphore:
                    items = await fetch_service.fetch_source(source, batch_id=batch.id)
                    return len(items)

            tasks = [fetch_with_semaphore(s) for s in sources_to_fetch]
            item_counts = await asyncio.gather(*tasks, return_exceptions=True)

            for source, count in zip(sources_to_fetch, item_counts):
                if isinstance(count, int) and count > 0:
                    source_names.append(source.name)
                    total_items += count

            batch.items_count = total_items
            batch.sources = json.dumps(source_names, ensure_ascii=False)

            await session.commit()

    async def refresh_source(self, source_id: int) -> None:
        import json as json_module
        from src.models import FetchBatch, Source
        from src.services.fetch_service import FetchService

        async with self.session_factory() as session:
            fetch_service = FetchService(session)
            result = await session.execute(
                select(Source).where(Source.id == source_id)
            )
            source = result.scalar_one_or_none()
            if source:
                batch = FetchBatch(items_count=0, sources=json_module.dumps([source.name]))
                session.add(batch)
                await session.flush()
                
                items = await fetch_service.fetch_source(source, batch_id=batch.id)
                batch.items_count = len(items)
                
                await session.commit()

    async def refresh_all(self) -> None:
        from src.services.fetch_service import FetchService

        async with self.session_factory() as session:
            fetch_service = FetchService(session)
            await fetch_service.fetch_all()

    async def refresh_group(self, group_id: int) -> None:
        import json as json_module
        from src.models import FetchBatch, Source, SourceGroup, SourceGroupMember
        from src.services.fetch_service import FetchService

        async with self.session_factory() as session:
            result = await session.execute(
                select(Source)
                .join(SourceGroupMember, SourceGroupMember.source_id == Source.id)
                .where(SourceGroupMember.group_id == group_id, Source.is_active == True, Source.deleted_at.is_(None))
            )
            sources = list(result.scalars().all())

            if not sources:
                return

            group_result = await session.execute(
                select(SourceGroup).where(SourceGroup.id == group_id)
            )
            group = group_result.scalar_one_or_none()
            group_info = [{"id": group.id, "name": group.name}] if group else []

            fetch_service = FetchService(session)
            batch = FetchBatch(
                items_count=0,
                sources=json_module.dumps([s.name for s in sources]),
                groups=json_module.dumps(group_info),
            )
            session.add(batch)
            await session.flush()

            total_items = 0
            for source in sources:
                items = await fetch_service.fetch_source(source, batch_id=batch.id)
                total_items += len(items)

            batch.items_count = total_items
            await session.commit()