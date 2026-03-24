"""TDD tests for ALL feed update paths creating FetchBatch."""

import json
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import FeedItem, FetchBatch, Source
from src.services.fetch_service import FetchService


@pytest_asyncio.fixture
async def test_source(db_session):
    source = Source(
        name="Test Source",
        url="https://test.example.com/feed",
        fetch_interval=1800,
        is_active=True,
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)
    return source


class TestFetchServiceFetchAll:
    """Test fetch_all creates FetchBatch."""

    @pytest.mark.asyncio
    async def test_fetch_all_creates_batch(self, db_session, test_source):
        fetch_service = FetchService(db_session)

        mock_rss = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel><title>Test</title>
                <item><title>Item 1</title><link>https://example.com/1</link></item>
            </channel>
        </rss>
        """

        with patch.object(fetch_service, "_fetch_with_retry", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_rss
            batch_id, results = await fetch_service.fetch_all()

        assert batch_id is not None
        assert batch_id > 0

        result = await db_session.execute(select(FetchBatch).where(FetchBatch.id == batch_id))
        batch = result.scalar_one()
        assert batch is not None
        assert batch.items_count > 0

    @pytest.mark.asyncio
    async def test_fetch_all_items_have_batch_id(self, db_session, test_source):
        fetch_service = FetchService(db_session)

        mock_rss = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel><title>Test</title>
                <item><title>Item 1</title><link>https://example.com/1</link></item>
                <item><title>Item 2</title><link>https://example.com/2</link></item>
            </channel>
        </rss>
        """

        with patch.object(fetch_service, "_fetch_with_retry", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_rss
            batch_id, results = await fetch_service.fetch_all()

        items = await db_session.execute(select(FeedItem))
        for item in items.scalars().all():
            assert item.batch_id == batch_id


class TestFetchServiceFetchSourceAutoBatch:
    """Test fetch_source creates FetchBatch when batch_id not provided."""

    @pytest.mark.asyncio
    async def test_fetch_source_without_batch_id_creates_batch(self, db_session, test_source):
        fetch_service = FetchService(db_session)

        mock_rss = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel><title>Test</title>
                <item><title>Item 1</title><link>https://example.com/1</link></item>
            </channel>
        </rss>
        """

        with patch.object(fetch_service, "_fetch_with_retry", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_rss
            items = await fetch_service.fetch_source(test_source, batch_id=None)

        result = await db_session.execute(select(FetchBatch))
        batches = result.scalars().all()

        assert len(batches) == 1, "FetchBatch should be created when batch_id not provided"
        assert batches[0].items_count == len(items)

    @pytest.mark.asyncio
    async def test_fetch_source_items_have_batch_id_when_auto_created(self, db_session, test_source):
        fetch_service = FetchService(db_session)

        mock_rss = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel><title>Test</title>
                <item><title>Item 1</title><link>https://example.com/1</link></item>
            </channel>
        </rss>
        """

        with patch.object(fetch_service, "_fetch_with_retry", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_rss
            items = await fetch_service.fetch_source(test_source, batch_id=None)

        for item in items:
            assert item.batch_id is not None


class TestHistoryAfterAnyFetch:
    """Test history returns data after any fetch."""

    @pytest.mark.asyncio
    async def test_history_after_fetch_all(self, db_session, test_source):
        fetch_service = FetchService(db_session)

        mock_rss = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel><title>Test</title>
                <item><title>Item 1</title><link>https://example.com/1</link></item>
            </channel>
        </rss>
        """

        with patch.object(fetch_service, "_fetch_with_retry", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_rss
            await fetch_service.fetch_all()

        result = await db_session.execute(select(FetchBatch).order_by(FetchBatch.created_at.desc()))
        batches = result.scalars().all()

        assert len(batches) >= 1

    @pytest.mark.asyncio
    async def test_history_after_fetch_source_without_batch_id(self, db_session, test_source):
        fetch_service = FetchService(db_session)

        mock_rss = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel><title>Test</title>
                <item><title>Item 1</title><link>https://example.com/1</link></item>
            </channel>
        </rss>
        """

        with patch.object(fetch_service, "_fetch_with_retry", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_rss
            await fetch_service.fetch_source(test_source, batch_id=None)

        result = await db_session.execute(select(FetchBatch).order_by(FetchBatch.created_at.desc()))
        batches = result.scalars().all()

        assert len(batches) >= 1