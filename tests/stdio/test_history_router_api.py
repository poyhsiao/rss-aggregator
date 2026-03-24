import pytest
import pytest_asyncio

from src.config import settings
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


class TestUpdateBatchName:
    @pytest.mark.asyncio
    async def test_update_batch_name_success(self, router, db_session, mock_api_key):
        from src.models import FetchBatch

        batch = FetchBatch(items_count=2, sources="[]")
        db_session.add(batch)
        await db_session.commit()

        request = JSONRPCRequest(
            jsonrpc="2.0",
            method=f"PATCH /api/v1/history/batches/{batch.id}/name",
            params={
                "headers": {"X-API-Key": mock_api_key},
                "body": {"name": "My Custom Name"},
            },
            id=1,
        )

        response = await router.route(request)

        assert response.result is not None
        assert response.result["status"] == 200
        body = response.result["body"]
        assert body["name"] == "My Custom Name"
        assert body["id"] == batch.id

    @pytest.mark.asyncio
    async def test_update_batch_name_returns_404_for_nonexistent_batch(
        self, router, db_session, mock_api_key
    ):
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="PATCH /api/v1/history/batches/99999/name",
            params={
                "headers": {"X-API-Key": mock_api_key},
                "body": {"name": "Test Name"},
            },
            id=1,
        )

        response = await router.route(request)

        assert response.result is not None
        assert response.result["status"] == 404

    @pytest.mark.asyncio
    async def test_update_batch_name_requires_name(self, router, db_session, mock_api_key):
        from src.models import FetchBatch

        batch = FetchBatch(items_count=0, sources="[]")
        db_session.add(batch)
        await db_session.commit()

        request = JSONRPCRequest(
            jsonrpc="2.0",
            method=f"PATCH /api/v1/history/batches/{batch.id}/name",
            params={
                "headers": {"X-API-Key": mock_api_key},
                "body": {},
            },
            id=1,
        )

        response = await router.route(request)

        assert response.result is not None
        assert response.result["status"] == 422

    @pytest.mark.asyncio
    async def test_update_batch_name_requires_api_key(self, router, db_session, monkeypatch):
        from src.models import FetchBatch

        monkeypatch.setattr(settings, "require_api_key", True)

        batch = FetchBatch(items_count=0, sources="[]")
        db_session.add(batch)
        await db_session.commit()

        request = JSONRPCRequest(
            jsonrpc="2.0",
            method=f"PATCH /api/v1/history/batches/{batch.id}/name",
            params={
                "headers": {},
                "body": {"name": "Test Name"},
            },
            id=1,
        )

        response = await router.route(request)

        assert response.error is not None
        assert response.error["code"] == -32603


class TestDeleteBatch:
    @pytest.mark.asyncio
    async def test_delete_batch_success(self, router, db_session, mock_api_key):
        from src.models import FetchBatch

        batch = FetchBatch(items_count=2, sources="[]")
        db_session.add(batch)
        await db_session.commit()

        batch_id = batch.id

        request = JSONRPCRequest(
            jsonrpc="2.0",
            method=f"DELETE /api/v1/history/batches/{batch_id}",
            params={"headers": {"X-API-Key": mock_api_key}},
            id=1,
        )

        response = await router.route(request)

        assert response.result is not None
        assert response.result["status"] == 200
        body = response.result["body"]
        assert body["success"] is True

        request_list = JSONRPCRequest(
            jsonrpc="2.0",
            method="GET /api/v1/history/batches",
            params={"headers": {"X-API-Key": mock_api_key}, "query": {}},
            id=2,
        )

        response_list = await router.route(request_list)
        body_list = response_list.result["body"]
        assert all(b["id"] != batch_id for b in body_list["batches"])

    @pytest.mark.asyncio
    async def test_delete_batch_returns_404_for_nonexistent_batch(
        self, router, db_session, mock_api_key
    ):
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="DELETE /api/v1/history/batches/99999",
            params={"headers": {"X-API-Key": mock_api_key}},
            id=1,
        )

        response = await router.route(request)

        assert response.result is not None
        assert response.result["status"] == 404

    @pytest.mark.asyncio
    async def test_delete_batch_requires_api_key(self, router, db_session, monkeypatch):
        from src.models import FetchBatch

        monkeypatch.setattr(settings, "require_api_key", True)

        batch = FetchBatch(items_count=0, sources="[]")
        db_session.add(batch)
        await db_session.commit()

        request = JSONRPCRequest(
            jsonrpc="2.0",
            method=f"DELETE /api/v1/history/batches/{batch.id}",
            params={"headers": {}},
            id=1,
        )

        response = await router.route(request)

        assert response.error is not None
        assert response.error["code"] == -32603