"""Tests for HistoryService."""

import pytest
from datetime import date, datetime

from src.models import FeedItem, Source
from src.services.history_service import HistoryService


@pytest.fixture
def history_service(db_session):
    """Create HistoryService instance."""
    return HistoryService(db_session)


@pytest.mark.asyncio
async def test_get_history_returns_empty_list_when_no_items(history_service):
    """Test that get_history returns empty list when no items exist."""
    items, pagination = await history_service.get_history()

    assert items == []
    assert pagination["total_items"] == 0
    assert pagination["total_pages"] == 0


@pytest.mark.asyncio
async def test_get_history_filters_by_date_range(db_session):
    """Test that get_history filters by date range."""
    source = Source(name="Test Source", url="https://example.com/feed.xml")
    db_session.add(source)
    await db_session.flush()

    old_item = FeedItem(
        source_id=source.id,
        title="Old Item",
        link="https://example.com/old",
        fetched_at=datetime(2024, 1, 10, 12, 0, 0),
    )
    new_item = FeedItem(
        source_id=source.id,
        title="New Item",
        link="https://example.com/new",
        fetched_at=datetime(2024, 1, 20, 12, 0, 0),
    )
    db_session.add_all([old_item, new_item])
    await db_session.commit()

    service = HistoryService(db_session)

    items, pagination = await service.get_history(
        start_date=date(2024, 1, 15),
        end_date=date(2024, 1, 25),
    )

    assert len(items) == 1
    assert items[0]["title"] == "New Item"
    assert pagination["total_items"] == 1
