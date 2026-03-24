"""Integration tests for history query functionality.

This test verifies the complete flow:
1. Database has FetchBatch and FeedItem records
2. HistoryService returns correct data
3. StdioRouter returns correct JSON-RPC response
4. Response format matches what frontend expects
"""

import json

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import APIKey, FeedItem, FetchBatch, Source
from src.services.history_service import HistoryService
from src.stdio.protocol import JSONRPCRequest
from src.stdio.router import StdioRouter


@pytest_asyncio.fixture
async def setup_test_data(db_session: AsyncSession):
    """Create complete test data for history query."""
    api_key = APIKey(key="test-integration-key", name="Integration Test Key", is_active=True)
    db_session.add(api_key)

    source = Source(name="BBC News", url="https://feeds.bbci.co.uk/news/rss.xml", is_active=True)
    db_session.add(source)
    await db_session.flush()

    batch = FetchBatch(items_count=3, sources='["BBC News"]')
    db_session.add(batch)
    await db_session.flush()

    items = [
        FeedItem(source_id=source.id, batch_id=batch.id, title=f"Article {i+1}", link=f"https://bbc.com/{i+1}")
        for i in range(3)
    ]
    db_session.add_all(items)
    await db_session.commit()

    return {"api_key": api_key.key, "source": source, "batch": batch, "items": items}


class TestHistoryQueryIntegration:
    """Integration tests for history query."""

    @pytest.mark.asyncio
    async def test_history_service_returns_correct_data(self, db_session: AsyncSession, setup_test_data):
        """Test that HistoryService returns data in correct format."""
        svc = HistoryService(db_session)

        result = await svc.get_history_batches()

        assert result.total_batches == 1
        assert result.total_items == 3
        assert len(result.batches) == 1

        batch = result.batches[0]
        assert batch.id == setup_test_data["batch"].id
        assert batch.items_count == 3
        assert batch.sources == ["BBC News"]

    @pytest.mark.asyncio
    async def test_history_service_get_items_by_batch(self, db_session: AsyncSession, setup_test_data):
        """Test that HistoryService returns items for a batch."""
        svc = HistoryService(db_session)

        items, pagination = await svc.get_history_by_batch(setup_test_data["batch"].id)

        assert pagination.total_items == 3
        assert len(items) == 3

        for item in items:
            assert item.source == "BBC News"
            assert item.title.startswith("Article")

    @pytest.mark.asyncio
    async def test_stdio_router_history_batches_endpoint(self, db_session: AsyncSession, setup_test_data):
        """Test that stdio router returns correct response format."""
        router = StdioRouter()

        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="GET /api/v1/history/batches",
            params={"headers": {"X-API-Key": setup_test_data["api_key"]}, "query": {}},
            id=1,
        )

        response = await router.route(request)

        assert response.result is not None
        assert response.result["status"] == 200

        body = response.result["body"]
        assert "batches" in body
        assert "total_batches" in body
        assert "total_items" in body

        assert body["total_batches"] == 1
        assert body["total_items"] == 3
        assert len(body["batches"]) == 1

        batch = body["batches"][0]
        assert "id" in batch
        assert "items_count" in batch
        assert "sources" in batch
        assert "created_at" in batch

    @pytest.mark.asyncio
    async def test_stdio_router_history_by_batch_endpoint(self, db_session: AsyncSession, setup_test_data):
        """Test that stdio router returns correct items for a batch."""
        router = StdioRouter()
        batch_id = setup_test_data["batch"].id

        request = JSONRPCRequest(
            jsonrpc="2.0",
            method=f"GET /api/v1/history/batches/{batch_id}",
            params={"headers": {"X-API-Key": setup_test_data["api_key"]}, "query": {}},
            id=1,
        )

        response = await router.route(request)

        assert response.result is not None
        assert response.result["status"] == 200

        body = response.result["body"]
        assert "items" in body
        assert "pagination" in body

        pagination = body["pagination"]
        assert pagination["total_items"] == 3
        assert pagination["total_pages"] == 1

        items = body["items"]
        assert len(items) == 3

        for item in items:
            assert "id" in item
            assert "title" in item
            assert "link" in item
            assert "source" in item

    @pytest.mark.asyncio
    async def test_response_format_matches_frontend_expectations(self, db_session: AsyncSession, setup_test_data):
        """Test that response format matches what HistoryPage.vue expects."""
        router = StdioRouter()

        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="GET /api/v1/history/batches",
            params={"headers": {"X-API-Key": setup_test_data["api_key"]}, "query": {}},
            id=1,
        )

        response = await router.route(request)
        body = response.result["body"]

        assert isinstance(body["batches"], list)
        assert isinstance(body["total_batches"], int)
        assert isinstance(body["total_items"], int)

        if body["batches"]:
            batch = body["batches"][0]
            assert isinstance(batch["id"], int)
            assert isinstance(batch["items_count"], int)
            assert isinstance(batch["sources"], list)
            assert isinstance(batch["created_at"], str)

    @pytest.mark.asyncio
    async def test_empty_result_when_no_batches(self, db_session: AsyncSession):
        """Test that empty result is handled correctly."""
        api_key = APIKey(key="empty-test-key", name="Empty Test Key", is_active=True)
        db_session.add(api_key)
        await db_session.commit()

        router = StdioRouter()

        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="GET /api/v1/history/batches",
            params={"headers": {"X-API-Key": api_key.key}, "query": {}},
            id=1,
        )

        response = await router.route(request)

        assert response.result["status"] == 200
        body = response.result["body"]
        assert body["batches"] == []
        assert body["total_batches"] == 0
        assert body["total_items"] == 0