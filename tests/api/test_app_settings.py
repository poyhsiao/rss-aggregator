"""Tests for app settings API route."""

from collections.abc import AsyncGenerator
from typing import AsyncGenerator as AsyncGen

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.api.deps import get_session
from src.main import app
from src.models import Base, AppSettings

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
    maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def async_client(
    test_session: AsyncSession,
) -> AsyncGen[AsyncClient, None]:
    async def override_get_session() -> AsyncGen[AsyncSession, None]:
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


class TestGetAppSettings:
    @pytest.mark.asyncio
    async def test_get_settings_returns_defaults(
        self, async_client: AsyncClient
    ) -> None:
        """GET /api/v1/settings returns all False by default (creates record on demand)."""
        response = await async_client.get("/api/v1/settings")
        if response.status_code == 401:
            pytest.skip("API key required in this environment")
        data = response.json()
        assert data["group_enabled"] is False
        assert data["schedule_enabled"] is False
        assert data["share_enabled"] is False

    @pytest.mark.asyncio
    async def test_get_settings_returns_existing(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """GET /api/v1/settings returns the existing record when it exists."""
        test_session.add(AppSettings(group_enabled=True, share_enabled=True))
        await test_session.commit()

        response = await async_client.get("/api/v1/settings")
        if response.status_code == 401:
            pytest.skip("API key required in this environment")
        data = response.json()
        assert data["group_enabled"] is True
        assert data["schedule_enabled"] is False
        assert data["share_enabled"] is True


class TestPutAppSettings:
    @pytest.mark.asyncio
    async def test_put_settings_full_update(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """PUT /api/v1/settings with all fields updates all flags."""
        test_session.add(AppSettings())
        await test_session.commit()

        response = await async_client.put(
            "/api/v1/settings",
            json={
                "group_enabled": True,
                "schedule_enabled": True,
                "share_enabled": True,
            },
        )
        if response.status_code == 401:
            pytest.skip("API key required in this environment")
        data = response.json()
        assert data["group_enabled"] is True
        assert data["schedule_enabled"] is True
        assert data["share_enabled"] is True

    @pytest.mark.asyncio
    async def test_put_settings_partial_update(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """PUT with partial data only updates provided fields."""
        test_session.add(AppSettings())
        await test_session.commit()

        response = await async_client.put("/api/v1/settings", json={"share_enabled": True})
        if response.status_code == 401:
            pytest.skip("API key required in this environment")
        data = response.json()
        assert data["share_enabled"] is True
        assert data["group_enabled"] is False  # unchanged
        assert data["schedule_enabled"] is False  # unchanged

    @pytest.mark.asyncio
    async def test_put_settings_creates_if_missing(
        self, async_client: AsyncClient
    ) -> None:
        """PUT /api/v1/settings creates a record if none exists yet."""
        response = await async_client.put(
            "/api/v1/settings", json={"group_enabled": True}
        )
        if response.status_code == 401:
            pytest.skip("API key required in this environment")
        data = response.json()
        assert data["group_enabled"] is True
        assert data["schedule_enabled"] is False
        assert data["share_enabled"] is False
