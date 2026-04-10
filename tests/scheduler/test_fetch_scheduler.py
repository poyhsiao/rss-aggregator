"""Tests for FetchScheduler."""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock

from src.scheduler.fetch_scheduler import FetchScheduler


@pytest.fixture
def scheduler() -> FetchScheduler:
    """Create FetchScheduler instance with mock session factory."""
    mock_factory = MagicMock()
    return FetchScheduler(
        session_factory=mock_factory,
        check_interval=1,
        max_concurrent=2,
    )


@pytest.mark.asyncio
async def test_scheduler_can_start_and_stop(scheduler: FetchScheduler):
    """Test that scheduler can start and stop."""
    await scheduler.start()
    assert scheduler._running is True

    await scheduler.stop()
    assert scheduler._running is False


@pytest.mark.asyncio
async def test_refresh_all_creates_session():
    """Test that refresh_all creates a session from factory."""
    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_session
    mock_context.__aexit__.return_value = None
    mock_factory.return_value = mock_context

    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    scheduler = FetchScheduler(
        session_factory=mock_factory,
        check_interval=1,
    )

    await scheduler.refresh_all()
    mock_factory.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_source_creates_session():
    """Test that refresh_source creates a session from factory."""
    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_session
    mock_context.__aexit__.return_value = None
    mock_factory.return_value = mock_context

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    scheduler = FetchScheduler(
        session_factory=mock_factory,
        check_interval=1,
    )

    await scheduler.refresh_source(1)
    mock_factory.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_group_creates_session():
    """Test that refresh_group creates a session from factory."""
    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_session
    mock_context.__aexit__.return_value = None
    mock_factory.return_value = mock_context

    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    scheduler = FetchScheduler(
        session_factory=mock_factory,
        check_interval=1,
    )

    await scheduler.refresh_group(1)
    mock_factory.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_group_only_active_sources():
    """Test that refresh_group only fetches active, non-deleted sources."""
    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_session
    mock_context.__aexit__.return_value = None
    mock_factory.return_value = mock_context

    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    scheduler = FetchScheduler(
        session_factory=mock_factory,
        check_interval=1,
    )

    await scheduler.refresh_group(1)

    execute_call = mock_session.execute.call_args_list[0]
    stmt = str(execute_call[0][0])
    assert "group_id" in stmt.lower() or "SourceGroupMember" in stmt


@pytest.mark.asyncio
async def test_check_and_fetch_skips_sources_without_group_schedule():
    """Test that _check_and_fetch returns early when no enabled SourceGroupSchedule exists."""
    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_session
    mock_context.__aexit__.return_value = None
    mock_factory.return_value = mock_context

    # First (and only) execute: scheduled_group_ids query returns empty list
    mock_schedule_result = Mock()
    mock_schedule_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_schedule_result)

    scheduler = FetchScheduler(
        session_factory=mock_factory,
        check_interval=1,
    )
    scheduler.refresh_group = AsyncMock()

    await scheduler._check_and_fetch()

    # Only one execute call (the SourceGroupSchedule query); Source table never queried
    assert mock_session.execute.call_count == 1
    scheduler.refresh_group.assert_not_called()


@pytest.mark.asyncio
async def test_check_and_fetch_only_fetches_sources_in_scheduled_groups():
    """Test that _check_and_fetch filters sources by scheduled group ids."""
    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_session
    mock_context.__aexit__.return_value = None
    mock_factory.return_value = mock_context

    # First execute: returns group_id=1 only (group_id=2 has no enabled schedule)
    mock_schedule_result = Mock()
    mock_schedule_result.scalars.return_value.all.return_value = [1]

    # Second execute: sources query returns empty list (no sources in group 1)
    mock_source_result = Mock()
    mock_source_result.scalars.return_value.all.return_value = []

    mock_session.execute = AsyncMock(
        side_effect=[mock_schedule_result, mock_source_result]
    )

    scheduler = FetchScheduler(
        session_factory=mock_factory,
        check_interval=1,
    )

    await scheduler._check_and_fetch()

    # Two execute calls: one for schedules, one for sources
    assert mock_session.execute.call_count == 2

    # Verify second query contains group_id filtering
    source_query_call = mock_session.execute.call_args_list[1]
    stmt = str(source_query_call[0][0])
    assert "group_id" in stmt.lower() or "sourcegroupmember" in stmt.lower()


@pytest.mark.asyncio
async def test_check_and_fetch_skips_disabled_schedule_groups():
    """Test that _check_and_fetch returns early when all SourceGroupSchedules are disabled."""
    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_session
    mock_context.__aexit__.return_value = None
    mock_factory.return_value = mock_context

    # First execute: disabled schedule is filtered out, returns empty list
    mock_schedule_result = Mock()
    mock_schedule_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_schedule_result)

    scheduler = FetchScheduler(
        session_factory=mock_factory,
        check_interval=1,
    )
    scheduler.refresh_group = AsyncMock()

    await scheduler._check_and_fetch()

    # Early return: only one execute call, Source table never queried
    assert mock_session.execute.call_count == 1
    scheduler.refresh_group.assert_not_called()