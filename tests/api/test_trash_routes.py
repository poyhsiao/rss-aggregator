"""Tests for trash API routes."""

from collections.abc import AsyncGenerator
from typing import AsyncGenerator as AsyncGen

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.api.deps import get_session, require_api_key
from src.main import app
from src.models import Base, Source

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGen[AsyncSession, None]:
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def async_client(test_session: AsyncSession) -> AsyncGen[AsyncClient, None]:
    async def override_get_session() -> AsyncGen[AsyncSession, None]:
        yield test_session

    async def override_require_api_key() -> str:
        return "test-api-key"

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[require_api_key] = override_require_api_key

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


class TestListTrash:
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_trash(
        self, async_client: AsyncClient
    ) -> None:
        response = await async_client.get("/api/v1/trash")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_returns_trash_items(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        source = Source(name="Trash Test", url="https://trash-test.com/rss")
        source.soft_delete()
        test_session.add(source)
        await test_session.commit()

        response = await async_client.get("/api/v1/trash")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Trash Test"


class TestRestoreSource:
    @pytest.mark.asyncio
    async def test_restore_no_conflict(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        source = Source(name="Restore Test", url="https://restore-test.com/rss")
        source.soft_delete()
        test_session.add(source)
        await test_session.commit()

        response = await async_client.post(f"/api/v1/trash/{source.id}/restore")

        assert response.status_code == 200
        data = response.json()
        assert data["restored"] is True
        assert data["name"] == "Restore Test"

    @pytest.mark.asyncio
    async def test_restore_conflict_returns_409(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        deleted = Source(name="Conflict Test", url="https://conflict-test.com/rss")
        deleted.soft_delete()
        test_session.add(deleted)

        existing = Source(name="New Conflict", url="https://conflict-test.com/rss")
        test_session.add(existing)
        await test_session.commit()

        response = await async_client.post(f"/api/v1/trash/{deleted.id}/restore")

        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["error"] == "conflict_detected"

    @pytest.mark.asyncio
    async def test_restore_with_overwrite(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        deleted = Source(name="Overwrite Test", url="https://overwrite-test.com/rss")
        deleted.soft_delete()
        test_session.add(deleted)

        existing = Source(name="Existing", url="https://overwrite-test.com/rss")
        test_session.add(existing)
        await test_session.commit()

        response = await async_client.post(
            f"/api/v1/trash/{deleted.id}/restore",
            json={"conflict_resolution": "overwrite"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["restored"] is True

    @pytest.mark.asyncio
    async def test_restore_with_keep_existing(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        deleted = Source(name="Keep Test", url="https://keep-test.com/rss")
        deleted.soft_delete()
        test_session.add(deleted)

        existing = Source(name="Existing", url="https://keep-test.com/rss")
        test_session.add(existing)
        await test_session.commit()

        response = await async_client.post(
            f"/api/v1/trash/{deleted.id}/restore",
            json={"conflict_resolution": "keep_existing"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["restored"] is False

    @pytest.mark.asyncio
    async def test_restore_not_found(self, async_client: AsyncClient) -> None:
        response = await async_client.post("/api/v1/trash/9999/restore")
        assert response.status_code == 404


class TestPermanentDelete:
    @pytest.mark.asyncio
    async def test_permanent_delete(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        source = Source(name="Permanent Delete", url="https://permanent.com/rss")
        source.soft_delete()
        test_session.add(source)
        await test_session.commit()
        source_id = source.id

        response = await async_client.delete(f"/api/v1/trash/{source_id}")

        assert response.status_code == 200
        assert response.json()["deleted"] is True

        result = await test_session.get(Source, source_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_permanent_delete_not_found(
        self, async_client: AsyncClient
    ) -> None:
        response = await async_client.delete("/api/v1/trash/9999")
        assert response.status_code == 404


class TestClearTrash:
    @pytest.mark.asyncio
    async def test_clear_trash(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        s1 = Source(name="Trash 1", url="https://trash1.com/rss")
        s1.soft_delete()
        s2 = Source(name="Trash 2", url="https://trash2.com/rss")
        s2.soft_delete()
        s3 = Source(name="Active", url="https://active.com/rss")
        test_session.add_all([s1, s2, s3])
        await test_session.commit()

        response = await async_client.delete("/api/v1/trash")

        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 2