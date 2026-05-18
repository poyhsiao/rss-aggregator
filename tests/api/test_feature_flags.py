"""Tests for feature flags API."""

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


class TestFeatureFlagsAPI:
    """Test feature flags API endpoints."""

    @pytest.mark.asyncio
    async def test_get_feature_flags(self, async_client: AsyncClient) -> None:
        """GET /api/v1/feature-flags returns all flags"""
        response = await async_client.get("/api/v1/feature-flags")
        assert response.status_code == 200
        data = response.json()
        assert "groups_enabled" in data
        assert "group_schedules_enabled" in data
        assert "source_group_schedules_enabled" in data
        assert isinstance(data["groups_enabled"], bool)

    @pytest.mark.asyncio
    async def test_put_feature_flags(self, async_client: AsyncClient) -> None:
        """PUT /api/v1/feature-flags updates flags"""
        response = await async_client.put(
            "/api/v1/feature-flags",
            json={"groups_enabled": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["groups_enabled"] is False

    @pytest.mark.asyncio
    async def test_put_feature_flags_batch(self, async_client: AsyncClient) -> None:
        """PUT /api/v1/feature-flags with multiple flags"""
        response = await async_client.put(
            "/api/v1/feature-flags",
            json={
                "groups_enabled": False,
                "group_schedules_enabled": False,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["groups_enabled"] is False
        assert data["group_schedules_enabled"] is False

    @pytest.mark.asyncio
    async def test_get_feature_flags_requires_auth(self, test_session: AsyncSession) -> None:
        """GET /api/v1/feature-flags requires API key"""
        async def override_get_session() -> AsyncGen[AsyncSession, None]:
            yield test_session

        async def override_require_api_key() -> str:
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="API key required")

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_api_key] = override_require_api_key

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/feature-flags")
            assert response.status_code == 401

        app.dependency_overrides.clear()