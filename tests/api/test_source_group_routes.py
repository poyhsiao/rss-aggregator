"""Tests for source group API routes."""

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


class TestCreateGroup:
    @pytest.mark.asyncio
    async def test_create_group(self, async_client: AsyncClient) -> None:
        resp = await async_client.post("/api/v1/source-groups", json={"name": "Tech"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Tech"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_duplicate_group_returns_409(
        self, async_client: AsyncClient
    ) -> None:
        await async_client.post("/api/v1/source-groups", json={"name": "Dup"})
        resp = await async_client.post("/api/v1/source-groups", json={"name": "Dup"})
        assert resp.status_code == 409


class TestListGroups:
    @pytest.mark.asyncio
    async def test_list_groups(self, async_client: AsyncClient) -> None:
        await async_client.post("/api/v1/source-groups", json={"name": "A"})
        await async_client.post("/api/v1/source-groups", json={"name": "B"})
        resp = await async_client.get("/api/v1/source-groups")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    @pytest.mark.asyncio
    async def test_list_groups_empty(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/api/v1/source-groups")
        assert resp.status_code == 200
        assert resp.json() == []


class TestUpdateGroup:
    @pytest.mark.asyncio
    async def test_update_group(self, async_client: AsyncClient) -> None:
        create_resp = await async_client.post(
            "/api/v1/source-groups", json={"name": "Old"}
        )
        gid = create_resp.json()["id"]
        resp = await async_client.put(
            f"/api/v1/source-groups/{gid}", json={"name": "New"}
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New"

    @pytest.mark.asyncio
    async def test_update_nonexistent_group_returns_404(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.put(
            "/api/v1/source-groups/9999", json={"name": "X"}
        )
        assert resp.status_code == 404


class TestDeleteGroup:
    @pytest.mark.asyncio
    async def test_delete_group(self, async_client: AsyncClient) -> None:
        create_resp = await async_client.post(
            "/api/v1/source-groups", json={"name": "ToDelete"}
        )
        gid = create_resp.json()["id"]
        resp = await async_client.delete(f"/api/v1/source-groups/{gid}")
        assert resp.status_code == 204
        resp = await async_client.get("/api/v1/source-groups")
        assert len(resp.json()) == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_group_returns_404(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.delete("/api/v1/source-groups/9999")
        assert resp.status_code == 404


class TestGroupSources:
    @pytest.mark.asyncio
    async def test_add_source_to_group(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        grp = await async_client.post(
            "/api/v1/source-groups", json={"name": "Tech"}
        )
        gid = grp.json()["id"]

        source = Source(name="Feed", url="https://example.com/rss")
        test_session.add(source)
        await test_session.commit()
        await test_session.refresh(source)

        resp = await async_client.post(
            f"/api/v1/source-groups/{gid}/sources",
            json={"source_id": source.id},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_remove_source_from_group(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        grp = await async_client.post(
            "/api/v1/source-groups", json={"name": "Tech"}
        )
        gid = grp.json()["id"]

        source = Source(name="Feed", url="https://example.com/rss")
        test_session.add(source)
        await test_session.commit()
        await test_session.refresh(source)

        await async_client.post(
            f"/api/v1/source-groups/{gid}/sources",
            json={"source_id": source.id},
        )
        resp = await async_client.delete(
            f"/api/v1/source-groups/{gid}/sources/{source.id}"
        )
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_get_group_sources(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        grp = await async_client.post(
            "/api/v1/source-groups", json={"name": "Tech"}
        )
        gid = grp.json()["id"]

        s1 = Source(name="F1", url="https://example.com/1.xml")
        s2 = Source(name="F2", url="https://example.com/2.xml")
        test_session.add_all([s1, s2])
        await test_session.commit()
        await test_session.refresh(s1)
        await test_session.refresh(s2)

        await async_client.post(
            f"/api/v1/source-groups/{gid}/sources",
            json={"source_id": s1.id},
        )
        await async_client.post(
            f"/api/v1/source-groups/{gid}/sources",
            json={"source_id": s2.id},
        )
        resp = await async_client.get(f"/api/v1/source-groups/{gid}/sources")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    @pytest.mark.asyncio
    async def test_add_nonexistent_source_returns_400(
        self, async_client: AsyncClient
    ) -> None:
        grp = await async_client.post(
            "/api/v1/source-groups", json={"name": "Tech"}
        )
        gid = grp.json()["id"]
        resp = await async_client.post(
            f"/api/v1/source-groups/{gid}/sources",
            json={"source_id": 9999},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_remove_nonmember_returns_404(
        self, async_client: AsyncClient
    ) -> None:
        grp = await async_client.post(
            "/api/v1/source-groups", json={"name": "Tech"}
        )
        gid = grp.json()["id"]
        resp = await async_client.delete(
            f"/api/v1/source-groups/{gid}/sources/9999"
        )
        assert resp.status_code == 404
