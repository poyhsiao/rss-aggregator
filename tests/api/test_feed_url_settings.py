"""Tests for GET/POST /settings/feed-url endpoints."""

from typing import AsyncGenerator as AsyncGen, AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.api.deps import get_session
from src.main import app
from src.models import Base

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
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


class TestFeedUrlSettings:
    """Test /settings/feed-url GET and POST endpoints."""

    async def test_get_returns_default_false(self, async_client: AsyncClient) -> None:
        """When no setting exists, should return enabled=false."""
        response = await async_client.get("/api/v1/settings/feed-url")
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False

    async def test_post_sets_enabled_true(self, async_client: AsyncClient) -> None:
        """POST should set enabled to true."""
        response = await async_client.post(
            "/api/v1/settings/feed-url",
            json={"enabled": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True

    async def test_get_returns_updated_value(self, async_client: AsyncClient) -> None:
        """GET should return the previously set value."""
        await async_client.post(
            "/api/v1/settings/feed-url",
            json={"enabled": True},
        )
        response = await async_client.get("/api/v1/settings/feed-url")
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True

    async def test_post_sets_enabled_false(self, async_client: AsyncClient) -> None:
        """POST should set enabled to false."""
        # First set to true
        await async_client.post(
            "/api/v1/settings/feed-url",
            json={"enabled": True},
        )
        # Then set to false
        response = await async_client.post(
            "/api/v1/settings/feed-url",
            json={"enabled": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False