"""Tests for HistoryService."""

import pytest
from datetime import date

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
