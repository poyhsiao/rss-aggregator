from datetime import datetime
from typing import List

from croniter import croniter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import SourceGroupSchedule
from src.utils.time import now as get_now


class DuplicateScheduleError(ValueError):
    pass


class SourceGroupScheduleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_schedule(
        self,
        group_id: int,
        cron_expression: str,
    ) -> SourceGroupSchedule:
        if not self._validate_cron(cron_expression):
            raise ValueError("Invalid cron expression")
        
        existing = await self._check_duplicate(group_id, cron_expression)
        if existing:
            raise DuplicateScheduleError("Duplicate schedule with same cron expression already exists")
        
        count_result = await self.session.execute(
            select(SourceGroupSchedule).where(
                SourceGroupSchedule.group_id == group_id
            )
        )
        existing_count = len(list(count_result.scalars().all()))
        if existing_count >= 10:
            raise ValueError("Maximum 10 schedules per group")
        
        schedule = SourceGroupSchedule(
            group_id=group_id,
            cron_expression=cron_expression,
        )
        self.session.add(schedule)
        await self.session.flush()
        
        schedule.next_run_at = self._calculate_next_run(cron_expression)
        
        await self.session.commit()
        await self.session.refresh(schedule)
        return schedule

    async def list_schedules(self, group_id: int) -> List[SourceGroupSchedule]:
        result = await self.session.execute(
            select(SourceGroupSchedule).where(
                SourceGroupSchedule.group_id == group_id
            )
        )
        return list(result.scalars().all())

    async def get_schedule(self, schedule_id: int) -> SourceGroupSchedule | None:
        result = await self.session.execute(
            select(SourceGroupSchedule).where(
                SourceGroupSchedule.id == schedule_id
            )
        )
        return result.scalar_one_or_none()

    async def update_schedule(
        self,
        schedule_id: int,
        cron_expression: str,
    ) -> SourceGroupSchedule:
        schedule = await self.get_schedule(schedule_id)
        if not schedule:
            raise ValueError("Schedule not found")
        
        if not self._validate_cron(cron_expression):
            raise ValueError("Invalid cron expression")
        
        existing = await self._check_duplicate(schedule.group_id, cron_expression, schedule_id)
        if existing:
            raise DuplicateScheduleError("Duplicate schedule exists")
        
        schedule.cron_expression = cron_expression
        schedule.next_run_at = self._calculate_next_run(cron_expression)
        
        await self.session.commit()
        await self.session.refresh(schedule)
        return schedule

    async def delete_schedule(self, schedule_id: int) -> None:
        schedule = await self.get_schedule(schedule_id)
        if not schedule:
            raise ValueError("Schedule not found")
        
        await self.session.delete(schedule)
        await self.session.commit()

    async def toggle_schedule(self, schedule_id: int) -> SourceGroupSchedule:
        schedule = await self.get_schedule(schedule_id)
        if not schedule:
            raise ValueError("Schedule not found")
        
        schedule.is_enabled = not schedule.is_enabled
        
        if schedule.is_enabled:
            schedule.next_run_at = self._calculate_next_run(schedule.cron_expression)
        else:
            schedule.next_run_at = None
        
        await self.session.commit()
        await self.session.refresh(schedule)
        return schedule

    def _validate_cron(self, cron: str) -> bool:
        try:
            parts = cron.split()
            if len(parts) != 5:
                return False
            croniter(cron, get_now())
            return True
        except (ValueError, KeyError):
            return False

    async def _check_duplicate(
        self,
        group_id: int,
        cron_expression: str,
        exclude_id: int | None = None,
    ) -> SourceGroupSchedule | None:
        query = select(SourceGroupSchedule).where(
            SourceGroupSchedule.group_id == group_id,
            SourceGroupSchedule.cron_expression == cron_expression,
        )
        if exclude_id:
            query = query.where(SourceGroupSchedule.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    def _calculate_next_run(self, cron_expression: str) -> datetime:
        cron = croniter(cron_expression, get_now())
        return cron.get_next(datetime)