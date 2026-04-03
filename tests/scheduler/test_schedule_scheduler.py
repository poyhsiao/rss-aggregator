"""Tests for ScheduleScheduler."""

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import SourceGroupSchedule
from src.scheduler.schedule_scheduler import ScheduleScheduler
from src.utils.time import now as get_now


@pytest.fixture
def mock_session_factory():
    factory = MagicMock()
    session = AsyncMock(spec=AsyncSession)
    factory.return_value.__aenter__ = AsyncMock(return_value=session)
    factory.return_value.__aexit__ = AsyncMock(return_value=False)
    return factory, session


@pytest.fixture
def mock_fetch_scheduler():
    fetch_scheduler = MagicMock()
    fetch_scheduler.refresh_group = AsyncMock()
    return fetch_scheduler


def create_schedule(group_id: int, cron: str, next_run_at, enabled: bool = True) -> SourceGroupSchedule:
    schedule = SourceGroupSchedule(
        group_id=group_id,
        cron_expression=cron,
        is_enabled=enabled,
        next_run_at=next_run_at,
    )
    schedule.id = group_id
    return schedule


class TestScheduleSchedulerStartStop:
    def test_start_creates_task(self, mock_session_factory, mock_fetch_scheduler):
        factory, _ = mock_session_factory
        scheduler = ScheduleScheduler(session_factory=factory, fetch_scheduler=mock_fetch_scheduler)

        async def run():
            await scheduler.start()
            assert scheduler._running is True
            assert scheduler._task is not None
            await scheduler.stop()

        asyncio.run(run())

    def test_stop_cancels_task(self, mock_session_factory, mock_fetch_scheduler):
        factory, _ = mock_session_factory
        scheduler = ScheduleScheduler(session_factory=factory, fetch_scheduler=mock_fetch_scheduler)

        async def run():
            await scheduler.start()
            await scheduler.stop()
            assert scheduler._running is False

        asyncio.run(run())

    def test_start_idempotent(self, mock_session_factory, mock_fetch_scheduler):
        factory, _ = mock_session_factory
        scheduler = ScheduleScheduler(session_factory=factory, fetch_scheduler=mock_fetch_scheduler)

        async def run():
            await scheduler.start()
            first_task = scheduler._task
            await scheduler.start()
            assert scheduler._task is first_task
            await scheduler.stop()

        asyncio.run(run())


class TestScheduleExecution:
    def test_executes_due_schedule(self, mock_session_factory, mock_fetch_scheduler):
        factory, session = mock_session_factory
        past_time = get_now() - timedelta(minutes=5)
        schedule = create_schedule(group_id=1, cron="*/15 * * * *", next_run_at=past_time)

        async def mock_execute(stmt):
            text = str(stmt)
            if "is_enabled" in text and "next_run_at" in text:
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = [schedule]
                return mock_result
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            return mock_result

        session.execute = AsyncMock(side_effect=mock_execute)

        scheduler = ScheduleScheduler(session_factory=factory, fetch_scheduler=mock_fetch_scheduler)

        async def run():
            await scheduler._check_and_execute()
            mock_fetch_scheduler.refresh_group.assert_called_once_with(1)
            assert schedule.next_run_at is not None
            assert schedule.next_run_at > get_now()

        asyncio.run(run())

    def test_skips_future_schedule(self, mock_session_factory, mock_fetch_scheduler):
        factory, session = mock_session_factory
        future_time = get_now() + timedelta(hours=1)
        schedule = create_schedule(group_id=1, cron="0 * * * *", next_run_at=future_time)

        async def mock_execute(stmt):
            text = str(stmt)
            if "is_enabled" in text and "next_run_at" in text:
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                return mock_result
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [schedule]
            return mock_result

        session.execute = AsyncMock(side_effect=mock_execute)

        scheduler = ScheduleScheduler(session_factory=factory, fetch_scheduler=mock_fetch_scheduler)

        async def run():
            await scheduler._check_and_execute()
            mock_fetch_scheduler.refresh_group.assert_not_called()

        asyncio.run(run())

    def test_skips_disabled_schedule(self, mock_session_factory, mock_fetch_scheduler):
        factory, session = mock_session_factory
        past_time = get_now() - timedelta(minutes=5)
        schedule = create_schedule(group_id=1, cron="*/15 * * * *", next_run_at=past_time, enabled=False)

        async def mock_execute(stmt):
            text = str(stmt)
            if "is_enabled" in text and "next_run_at" in text:
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                return mock_result
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [schedule]
            return mock_result

        session.execute = AsyncMock(side_effect=mock_execute)

        scheduler = ScheduleScheduler(session_factory=factory, fetch_scheduler=mock_fetch_scheduler)

        async def run():
            await scheduler._check_and_execute()
            mock_fetch_scheduler.refresh_group.assert_not_called()

        asyncio.run(run())

    def test_continues_on_refresh_failure(self, mock_session_factory, mock_fetch_scheduler):
        factory, session = mock_session_factory
        past_time = get_now() - timedelta(minutes=5)
        schedule = create_schedule(group_id=1, cron="*/15 * * * *", next_run_at=past_time)

        async def mock_execute(stmt):
            text = str(stmt)
            if "is_enabled" in text and "next_run_at" in text:
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = [schedule]
                return mock_result
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            return mock_result

        session.execute = AsyncMock(side_effect=mock_execute)
        mock_fetch_scheduler.refresh_group.side_effect = Exception("Network error")

        scheduler = ScheduleScheduler(session_factory=factory, fetch_scheduler=mock_fetch_scheduler)

        async def run():
            await scheduler._check_and_execute()
            mock_fetch_scheduler.refresh_group.assert_called_once_with(1)
            assert schedule.next_run_at is not None

        asyncio.run(run())

    def test_executes_multiple_due_schedules(self, mock_session_factory, mock_fetch_scheduler):
        factory, session = mock_session_factory
        past_time = get_now() - timedelta(minutes=5)
        schedule1 = create_schedule(group_id=1, cron="*/15 * * * *", next_run_at=past_time)
        schedule2 = create_schedule(group_id=2, cron="0 * * * *", next_run_at=past_time)

        async def mock_execute(stmt):
            text = str(stmt)
            if "is_enabled" in text and "next_run_at" in text:
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = [schedule1, schedule2]
                return mock_result
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            return mock_result

        session.execute = AsyncMock(side_effect=mock_execute)

        scheduler = ScheduleScheduler(session_factory=factory, fetch_scheduler=mock_fetch_scheduler)

        async def run():
            await scheduler._check_and_execute()
            assert mock_fetch_scheduler.refresh_group.call_count == 2
            mock_fetch_scheduler.refresh_group.assert_any_call(1)
            mock_fetch_scheduler.refresh_group.assert_any_call(2)

        asyncio.run(run())
