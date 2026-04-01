"""TDD tests for history preservation after refresh."""

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


class TestHistoryPreservation:
    """Test that history items are preserved after refresh."""

    @pytest.mark.asyncio
    async def test_history_items_preserved_after_refresh(self, db_session, test_source):
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

        result = await db_session.execute(select(FetchBatch))
        first_batch = result.scalars().first()
        first_batch_id = first_batch.id

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

        items, pagination = await history_service.get_history_by_batch(first_batch_id)
        assert len(items) == 1, "First batch should still have items after second refresh"
        assert items[0].title == "Item Batch 1"

    @pytest.mark.asyncio
    async def test_all_batches_have_items_after_multiple_refreshes(self, db_session, test_source):
        fetch_service = FetchService(db_session)

        for i in range(1, 4):
            mock_rss = f"""<?xml version="1.0"?>
            <rss version="2.0">
                <channel><title>Test</title>
                    <item><title>Item {i}</title><link>https://example.com/{i}</link></item>
                </channel>
            </rss>
            """

            with patch.object(fetch_service, "_fetch_with_retry", new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = mock_rss
                await fetch_service.fetch_all()

        result = await db_session.execute(select(FetchBatch).order_by(FetchBatch.id))
        batches = list(result.scalars().all())
        assert len(batches) == 3

        history_service = HistoryService(db_session)

        for i, batch in enumerate(batches, 1):
            items, pagination = await history_service.get_history_by_batch(batch.id)
            assert len(items) == 1, f"Batch {batch.id} should have items"
            assert items[0].title == f"Item {i}"

    @pytest.mark.asyncio
    async def test_total_items_count_includes_soft_deleted(self, db_session, test_source):
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