"""Tests for FetchScheduler."""

import pytest
from unittest.mock import AsyncMock

from src.scheduler.fetch_scheduler import FetchScheduler


@pytest.fixture
def mock_fetch_service():
    """Create mock fetch service."""
    return AsyncMock()


@pytest.fixture
def scheduler(mock_fetch_service) -> FetchScheduler:
    """Create FetchScheduler instance."""
    return FetchScheduler(
        fetch_service=mock_fetch_service,
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
async def test_refresh_all_calls_fetch_all(scheduler: FetchScheduler, mock_fetch_service):
    """Test that refresh_all calls fetch_service.fetch_all."""
    await scheduler.refresh_all()
    mock_fetch_service.fetch_all.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_source_calls_fetch_source(scheduler: FetchScheduler, mock_fetch_service):
    """Test that refresh_source calls fetch_service.fetch_source."""
    from src.models import Source

    mock_source = Source(name="Test", url="https://example.com/feed.xml")
    mock_fetch_service.get_source.return_value = mock_source

    await scheduler.refresh_source(1)
    mock_fetch_service.get_source.assert_called_once_with(1)
    mock_fetch_service.fetch_source.assert_called_once_with(mock_source)