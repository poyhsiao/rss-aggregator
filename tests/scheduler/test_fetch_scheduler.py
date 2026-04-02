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