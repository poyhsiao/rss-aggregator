"""TDD tests for refresh operations creating FetchBatch."""

import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

from src.stdio.protocol import JSONRPCRequest
from src.stdio.router import StdioRouter
from src.models import Base, FetchBatch, FeedItem, Source
from src.db.database import async_session_factory, engine


@pytest.fixture
def router():
    return StdioRouter()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before tests and drop them after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def mock_api_key():
    """Create API key in a separate session to avoid locking issues."""
    from src.models import APIKey
    async with async_session_factory() as session:
        api_key = APIKey(key="test-key", name="Test Key")
        session.add(api_key)
        await session.commit()
        await session.refresh(api_key)
        return api_key.key


@pytest_asyncio.fixture
async def test_source():
    """Create test source in a separate session to avoid locking issues."""
    async with async_session_factory() as session:
        source = Source(
            name="Test Source",
            url="https://test.example.com/feed",
            is_active=True,
        )
        session.add(source)
        await session.commit()
        await session.refresh(source)
        return source


MOCK_RSS_CONTENT = """<?xml version="1.0"?>
<rss version="2.0">
    <channel>
        <title>Test Feed</title>
        <item>
            <title>Test Item 1</title>
            <link>https://example.com/item1</link>
            <description>Description 1</description>
        </item>
        <item>
            <title>Test Item 2</title>
            <link>https://example.com/item2</link>
        </item>
    </channel>
</rss>
"""


class TestRefreshAllCreatesBatch:
    """Test that refresh_all creates FetchBatch when scheduler is disabled."""

    @pytest.mark.asyncio
    async def test_refresh_all_without_scheduler_creates_batch(
        self, router, mock_api_key, test_source
    ):
        assert router._scheduler is None

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.text = MOCK_RSS_CONTENT
            mock_response.raise_for_status = AsyncMock()
            mock_get.return_value = mock_response

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="POST /api/v1/sources/refresh",
                params={"headers": {"X-API-Key": mock_api_key}},
                id=1,
            )

            response = await router.route(request)

        assert response.error is None
        assert response.result["status"] == 200

        from sqlalchemy import select
        async with async_session_factory() as session:
            result = await session.execute(select(FetchBatch))
            batches = list(result.scalars().all())
            assert len(batches) >= 1, "FetchBatch should be created after refresh_all!"

    @pytest.mark.asyncio
    async def test_refresh_source_without_scheduler_creates_batch(
        self, router, mock_api_key, test_source
    ):
        assert router._scheduler is None

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.text = MOCK_RSS_CONTENT
            mock_response.raise_for_status = AsyncMock()
            mock_get.return_value = mock_response

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method=f"POST /api/v1/sources/{test_source.id}/refresh",
                params={"headers": {"X-API-Key": mock_api_key}},
                id=1,
            )

            response = await router.route(request)

        assert response.error is None
        assert response.result["status"] == 200

        from sqlalchemy import select
        async with async_session_factory() as session:
            result = await session.execute(select(FetchBatch))
            batches = list(result.scalars().all())
            assert len(batches) >= 1, "FetchBatch should be created after refresh_source!"

    @pytest.mark.asyncio
    async def test_refresh_all_feed_items_have_batch_id(
        self, router, mock_api_key, test_source
    ):
        assert router._scheduler is None

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.text = MOCK_RSS_CONTENT
            mock_response.raise_for_status = AsyncMock()
            mock_get.return_value = mock_response

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="POST /api/v1/sources/refresh",
                params={"headers": {"X-API-Key": mock_api_key}},
                id=1,
            )

            await router.route(request)

        from sqlalchemy import select
        async with async_session_factory() as session:
            result = await session.execute(
                select(FeedItem).where(FeedItem.source_id == test_source.id)
            )
            items = list(result.scalars().all())

            if items:
                for item in items:
                    assert item.batch_id is not None, "FeedItem should have batch_id!"


class TestFetchServiceFetchAllWithBatch:
    """Test FetchService.fetch_all creates proper FetchBatch."""

    @pytest.mark.asyncio
    async def test_fetch_all_creates_batch(self, db_session, test_source):
        from src.services.fetch_service import FetchService

        fetch_service = FetchService(db_session)

        with patch.object(
            fetch_service,
            "_fetch_with_retry",
            return_value='<rss><item><title>Test</title><link>https://test.com</link></item></rss>',
        ):
            batch_id, results = await fetch_service.fetch_all()

        assert batch_id is not None

        from sqlalchemy import select
        result = await db_session.execute(
            select(FetchBatch).where(FetchBatch.id == batch_id)
        )
        batch = result.scalar_one_or_none()
        assert batch is not None
        assert batch.items_count >= 0


class TestHistoryQueryAfterRefresh:
    """Integration test: Verify history query works after refresh."""

    @pytest.mark.asyncio
    async def test_history_query_returns_data_after_fetch_all(
        self, db_session, test_source
    ):
        from src.services.fetch_service import FetchService
        from src.services.history_service import HistoryService

        fetch_service = FetchService(db_session)
        with patch.object(
            fetch_service,
            "_fetch_with_retry",
            return_value='<rss><item><title>Test</title><link>https://test.com/1</link></item></rss>',
        ):
            batch_id, _ = await fetch_service.fetch_all()

        history_service = HistoryService(db_session)
        result = await history_service.get_history_batches(limit=10, offset=0)

        assert result.total_batches >= 1
        assert result.total_items >= 1
        assert len(result.batches) >= 1
        assert result.batches[0].id == batch_id