"""TDD tests for history behavior after refresh (soft-delete mode)."""

import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

from sqlalchemy import select

from src.models import FeedItem, FetchBatch, Source
from src.services.fetch_service import FetchService
from src.services.history_service import HistoryService


@pytest_asyncio.fixture
async def test_source(db_session):
    source = Source(
        name="Test Source",
        url="https://test.example.com/feed",
        is_active=True,
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)
    return source


class TestHistoryAfterRefresh:
    """Test history behavior after refresh with soft-delete."""

    @pytest.mark.asyncio
    async def test_latest_batch_has_items_after_refresh(self, db_session, test_source):
        """Test that the latest batch has items after a second refresh."""
        fetch_service = FetchService(db_session)

        mock_rss_1 = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel><title>Test</title>
                <item><title>Item Batch 1</title><link>https://example.com/1</link></item>
            </channel>
        </rss>
        """

        with patch.object(fetch_service, "_fetch_with_retry", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_rss_1
            await fetch_service.fetch_all()

        result = await db_session.execute(select(FetchBatch).order_by(FetchBatch.id))
        batches = list(result.scalars().all())
        assert len(batches) == 1
        first_batch_id = batches[0].id

        history_service = HistoryService(db_session)
        items, pagination = await history_service.get_history_by_batch(first_batch_id)
        assert len(items) == 1
        assert items[0].title == "Item Batch 1"

        mock_rss_2 = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel><title>Test</title>
                <item><title>Item Batch 2</title><link>https://example.com/2</link></item>
            </channel>
        </rss>
        """

        with patch.object(fetch_service, "_fetch_with_retry", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_rss_2
            await fetch_service.fetch_all()

        result = await db_session.execute(select(FetchBatch).order_by(FetchBatch.id))
        all_batches = list(result.scalars().all())
        assert len(all_batches) == 2

        latest_batch = all_batches[-1]
        items, pagination = await history_service.get_history_by_batch(latest_batch.id)
        assert len(items) == 1
        assert items[0].title == "Item Batch 2"

    @pytest.mark.asyncio
    async def test_old_batch_items_preserved_on_refetch(self, db_session, test_source):
        """Test that old batch items are soft-deleted but still queryable."""
        fetch_service = FetchService(db_session)

        mock_rss_1 = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel><title>Test</title>
                <item><title>Item 1</title><link>https://example.com/1</link></item>
            </channel>
        </rss>
        """

        with patch.object(fetch_service, "_fetch_with_retry", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_rss_1
            await fetch_service.fetch_all()

        result = await db_session.execute(select(FetchBatch).order_by(FetchBatch.id))
        first_batch = list(result.scalars().all())[0]

        history_service = HistoryService(db_session)
        items, _ = await history_service.get_history_by_batch(first_batch.id)
        assert len(items) == 1

        mock_rss_2 = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel><title>Test</title>
                <item><title>Item 2</title><link>https://example.com/2</link></item>
            </channel>
        </rss>
        """

        with patch.object(fetch_service, "_fetch_with_retry", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_rss_2
            await fetch_service.fetch_all()

        items, _ = await history_service.get_history_by_batch(first_batch.id)
        assert len(items) == 1, "Old batch items should be preserved (soft-deleted)"
        assert items[0].title == "Item 1"

    @pytest.mark.asyncio
    async def test_total_items_counts_all_items_including_soft_deleted(self, db_session, test_source):
        """Test that total items counts all items including soft-deleted ones."""
        fetch_service = FetchService(db_session)

        mock_rss_1 = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel><title>Test</title>
                <item><title>Item 1</title><link>https://example.com/1</link></item>
                <item><title>Item 2</title><link>https://example.com/2</link></item>
            </channel>
        </rss>
        """

        with patch.object(fetch_service, "_fetch_with_retry", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_rss_1
            await fetch_service.fetch_all()

        mock_rss_2 = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel><title>Test</title>
                <item><title>Item 3</title><link>https://example.com/3</link></item>
            </channel>
        </rss>
        """

        with patch.object(fetch_service, "_fetch_with_retry", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_rss_2
            await fetch_service.fetch_all()

        history_service = HistoryService(db_session)
        response = await history_service.get_history_batches()

        assert response.total_items == 3, "Total items should count all items including soft-deleted"
