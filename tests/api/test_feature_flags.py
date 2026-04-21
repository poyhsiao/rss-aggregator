"""Tests for feature flags API routes."""

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


class TestGetFeatureFlags:
    """Test GET /api/v1/feature-flags endpoint."""

    @pytest.mark.asyncio
    async def test_get_feature_flags_returns_default_flags(
        self, async_client: AsyncClient
    ) -> None:
        """Test that GET returns all three default flags with false values."""
        resp = await async_client.get("/api/v1/feature-flags")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3

        flags = {f["key"]: f["enabled"] for f in data}
        assert flags["feature_groups"] is False
        assert flags["feature_schedules"] is False
        assert flags["feature_share_links"] is False

    @pytest.mark.asyncio
    async def test_get_feature_flags_contains_required_fields(
        self, async_client: AsyncClient
    ) -> None:
        """Test that each flag has all required fields."""
        resp = await async_client.get("/api/v1/feature-flags")
        assert resp.status_code == 200
        data = resp.json()

        for flag in data:
            assert "key" in flag
            assert "enabled" in flag
            assert flag["key"] in [
                "feature_groups",
                "feature_schedules",
                "feature_share_links",
            ]


class TestPatchFeatureFlags:
    """Test PATCH /api/v1/feature-flags endpoint."""

    @pytest.mark.asyncio
    async def test_patch_updates_flag_value(self, async_client: AsyncClient) -> None:
        """Test that PATCH can update a flag value."""
        resp = await async_client.patch(
            "/api/v1/feature-flags",
            json={"key": "feature_groups", "value": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["key"] == "feature_groups"
        assert data["enabled"] is True

    @pytest.mark.asyncio
    async def test_patch_multiple_flags(self, async_client: AsyncClient) -> None:
        """Test that PATCH can update multiple flags."""
        await async_client.patch(
            "/api/v1/feature-flags",
            json={"key": "feature_groups", "value": True},
        )
        resp = await async_client.patch(
            "/api/v1/feature-flags",
            json={"key": "feature_schedules", "value": True},
        )
        assert resp.status_code == 200

        get_resp = await async_client.get("/api/v1/feature-flags")
        flags = {f["key"]: f["enabled"] for f in get_resp.json()}
        assert flags["feature_groups"] is True
        assert flags["feature_schedules"] is True
        assert flags["feature_share_links"] is False

    @pytest.mark.asyncio
    async def test_patch_invalid_flag_name_returns_400(
        self, async_client: AsyncClient
    ) -> None:
        """Test that PATCH rejects invalid flag names."""
        resp = await async_client.patch(
            "/api/v1/feature-flags",
            json={"key": "invalid_flag", "value": True},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_patch_missing_key_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        """Test that PATCH without key returns validation error."""
        resp = await async_client.patch(
            "/api/v1/feature-flags",
            json={"value": True},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_patch_missing_value_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        """Test that PATCH without value returns validation error."""
        resp = await async_client.patch(
            "/api/v1/feature-flags",
            json={"key": "feature_groups"},
        )
        assert resp.status_code == 422


class TestFeatureFlagsPersistence:
    """Test that feature flags persist in database."""

    @pytest.mark.asyncio
    async def test_flags_persist_after_restart(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """Test that updated flag values persist in database."""
        # Update a flag
        await async_client.patch(
            "/api/v1/feature-flags",
            json={"key": "feature_share_links", "value": True},
        )

        # Verify it's in the database directly
        from src.models.feature_flag import FeatureFlag

        result = await test_session.execute(
            pytest.importorskip("sqlalchemy").select(FeatureFlag).where(
                FeatureFlag.key == "feature_share_links"
            )
        )
        flag = result.scalar_one_or_none()
        assert flag is not None
        assert flag.enabled is True