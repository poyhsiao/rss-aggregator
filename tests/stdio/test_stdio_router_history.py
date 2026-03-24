"""Tests for history routes in stdio router."""

import pytest
import pytest_asyncio

from src.stdio.protocol import JSONRPCRequest
from src.stdio.router import StdioRouter


@pytest.fixture
def router():
    return StdioRouter()


@pytest_asyncio.fixture
async def mock_api_key(db_session):
    from src.models import APIKey

    api_key = APIKey(key="test-key", name="Test Key")
    db_session.add(api_key)
    await db_session.commit()
    return api_key.key


@pytest.mark.asyncio
async def test_get_history_batches_returns_empty_when_no_batches(
    router, db_session, mock_api_key
):
    request = JSONRPCRequest(
        jsonrpc="2.0",
        method="GET /api/v1/history/batches",
        params={"headers": {"X-API-Key": mock_api_key}, "query": {}},
        id=1,
    )

    response = await router.route(request)

    assert response.result is not None
    assert response.result["status"] == 200
    body = response.result["body"]
    assert body["batches"] == []
    assert body["total_batches"] == 0
    assert body["total_items"] == 0


@pytest.mark.asyncio
async def test_get_history_batches_returns_batches_with_items(
    router, db_session, mock_api_key
):
    from src.models import FeedItem, FetchBatch, Source

    source = Source(name="Test Source", url="https://example.com/feed.xml")
    db_session.add(source)
    await db_session.flush()

    batch = FetchBatch(items_count=2, sources='["https://example.com/feed.xml"]')
    db_session.add(batch)
    await db_session.flush()

    item1 = FeedItem(
        source_id=source.id,
        title="Item 1",
        link="https://example.com/1",
        batch_id=batch.id,
    )
    item2 = FeedItem(
        source_id=source.id,
        title="Item 2",
        link="https://example.com/2",
        batch_id=batch.id,
    )
    db_session.add_all([item1, item2])
    await db_session.commit()

    request = JSONRPCRequest(
        jsonrpc="2.0",
        method="GET /api/v1/history/batches",
        params={"headers": {"X-API-Key": mock_api_key}, "query": {}},
        id=1,
    )

    response = await router.route(request)

    assert response.result is not None
    assert response.result["status"] == 200
    body = response.result["body"]
    assert len(body["batches"]) == 1
    assert body["batches"][0]["items_count"] == 2


@pytest.mark.asyncio
async def test_get_history_batches_supports_pagination(
    router, db_session, mock_api_key
):
    from src.models import FetchBatch

    for i in range(3):
        batch = FetchBatch(items_count=i, sources="[]")
        db_session.add(batch)
    await db_session.commit()

    request = JSONRPCRequest(
        jsonrpc="2.0",
        method="GET /api/v1/history/batches",
        params={
            "headers": {"X-API-Key": mock_api_key},
            "query": {"limit": 2, "offset": 0},
        },
        id=1,
    )

    response = await router.route(request)

    assert response.result is not None
    assert response.result["status"] == 200
    body = response.result["body"]
    assert len(body["batches"]) == 2


@pytest.mark.asyncio
async def test_get_history_by_batch_returns_items(router, db_session, mock_api_key):
    from src.models import FeedItem, FetchBatch, Source

    source = Source(name="Test Source", url="https://example.com/feed.xml")
    db_session.add(source)
    await db_session.flush()

    batch = FetchBatch(items_count=2, sources="[]")
    db_session.add(batch)
    await db_session.flush()

    item = FeedItem(
        source_id=source.id,
        title="Test Item",
        link="https://example.com/item",
        batch_id=batch.id,
    )
    db_session.add(item)
    await db_session.commit()

    request = JSONRPCRequest(
        jsonrpc="2.0",
        method=f"GET /api/v1/history/batches/{batch.id}",
        params={"headers": {"X-API-Key": mock_api_key}, "query": {}},
        id=1,
    )

    response = await router.route(request)

    assert response.result is not None
    assert response.result["status"] == 200
    body = response.result["body"]
    assert "items" in body
    assert "pagination" in body


@pytest.mark.asyncio
async def test_get_history_by_batch_returns_404_for_nonexistent_batch(
    router, db_session, mock_api_key
):
    request = JSONRPCRequest(
        jsonrpc="2.0",
        method="GET /api/v1/history/batches/99999",
        params={"headers": {"X-API-Key": mock_api_key}, "query": {}},
        id=1,
    )

    response = await router.route(request)

    assert response.result is not None
    assert response.result["status"] == 200
    body = response.result["body"]
    assert body["items"] == []
    assert body["pagination"]["total_items"] == 0


@pytest.mark.asyncio
async def test_get_history_batches_returns_error_without_api_key(router):
    request = JSONRPCRequest(
        jsonrpc="2.0",
        method="GET /api/v1/history/batches",
        params={"headers": {}, "query": {}},
        id=1,
    )

    response = await router.route(request)

    assert response.error is not None
    assert response.error["code"] == -32603