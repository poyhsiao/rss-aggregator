import asyncio
import logging
from datetime import datetime

from croniter import croniter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.models import SourceGroupSchedule
from src.utils.time import now as get_now

logger = logging.getLogger(__name__)


class ScheduleScheduler:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        fetch_scheduler,
    ) -> None:
        self.session_factory = session_factory
        self.fetch_scheduler = fetch_scheduler
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Schedule scheduler started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Schedule scheduler stopped")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                await self._check_and_execute()
            except Exception as e:
                logger.error(f"Schedule scheduler error: {e}")

            await asyncio.sleep(60)

    async def _check_and_execute(self) -> None:
        async with self.session_factory() as session:
            # Check feature flags before executing any schedules
            from src.models.feature_flag import FeatureFlag
            from sqlalchemy import select

            flag_result = await session.execute(
                select(FeatureFlag).where(FeatureFlag.key.in_(["feature_schedules", "feature_groups"]))
            )
            flags = {f.key: f.enabled for f in flag_result.scalars().all()}

            # If either flag is disabled, skip schedule execution but still calculate next run times
            if not flags.get("feature_schedules", False) or not flags.get("feature_groups", False):
                logger.debug("Schedules or groups feature disabled — skipping schedule execution")
                return

            now = get_now()
            result = await session.execute(
                select(SourceGroupSchedule).where(
                    SourceGroupSchedule.is_enabled == True,
                    SourceGroupSchedule.next_run_at <= now,
                )
            )
            schedules = list(result.scalars().all())

            schedules_by_group: dict[int, list[SourceGroupSchedule]] = {}
            for schedule in schedules:
                schedules_by_group.setdefault(schedule.group_id, []).append(schedule)

            for group_schedules in schedules_by_group.values():
                await self._execute_schedule(group_schedules[0], session)
                for s in group_schedules[1:]:
                    s.next_run_at = self._calculate_next_run(s.cron_expression)
                await session.commit()

    async def _execute_schedule(self, schedule: SourceGroupSchedule, session: AsyncSession) -> None:
        try:
            logger.info(f"Executing schedule {schedule.id} for group {schedule.group_id}")
            await self.fetch_scheduler.refresh_group(schedule.group_id)
        except Exception as e:
            logger.error(f"Failed to execute schedule {schedule.id}: {e}")

        schedule.next_run_at = self._calculate_next_run(schedule.cron_expression)

    def _calculate_next_run(self, cron_expression: str) -> datetime:
        cron = croniter(cron_expression, get_now())
        return cron.get_next(datetime)