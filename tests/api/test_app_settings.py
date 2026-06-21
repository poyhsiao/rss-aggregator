"""Tests for app settings API route."""

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
        assert data["source_group_schedules_enabled"] is False

    @pytest.mark.asyncio
    async def test_get_settings_returns_existing(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """GET /api/v1/settings returns the existing record when it exists."""
        test_session.add(AppSettings(group_enabled=True, share_enabled=True, source_group_schedules_enabled=True))
        await test_session.commit()

        response = await async_client.get("/api/v1/settings")
        if response.status_code == 401:
            pytest.skip("API key required in this environment")
        data = response.json()
        assert data["group_enabled"] is True
        assert data["schedule_enabled"] is False
        assert data["share_enabled"] is True
        assert data["source_group_schedules_enabled"] is True


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
                "source_group_schedules_enabled": True,
            },
        )
        if response.status_code == 401:
            pytest.skip("API key required in this environment")
        data = response.json()
        assert data["group_enabled"] is True
        assert data["schedule_enabled"] is True
        assert data["share_enabled"] is True
        assert data["source_group_schedules_enabled"] is True

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
        assert data["source_group_schedules_enabled"] is False  # unchanged

    @pytest.mark.asyncio
    async def test_put_settings_creates_if_missing(
        self, async_client: AsyncClient
    ) -> None:
        """PUT /api/v1/settings creates a record if none exists yet."""
        response = await async_client.put(
            "/api/v1/settings", json={"group_enabled": True, "source_group_schedules_enabled": True}
        )
        if response.status_code == 401:
            pytest.skip("API key required in this environment")
        data = response.json()
        assert data["group_enabled"] is True
        assert data["schedule_enabled"] is False
        assert data["share_enabled"] is False
        assert data["source_group_schedules_enabled"] is True

    @pytest.mark.asyncio
    async def test_put_settings_persists_to_database(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """PUT /api/v1/settings actually writes to the database, not just in-memory."""
        # Create initial record
        response = await async_client.put("/api/v1/settings", json={"share_enabled": True})
        if response.status_code == 401:
            pytest.skip("API key required in this environment")
        assert response.json()["share_enabled"] is True

        # Verify directly in the database (bypass FastAPI)
        from sqlalchemy import select
        result = await test_session.execute(select(AppSettings))
        saved = result.scalars().first()
        assert saved is not None
        assert saved.share_enabled is True

        # Toggle back off
        response2 = await async_client.put("/api/v1/settings", json={"share_enabled": False})
        data2 = response2.json()
        assert data2["share_enabled"] is False

        # Re-fetch from API to confirm persistence
        response3 = await async_client.get("/api/v1/settings")
        assert response3.json()["share_enabled"] is False

    @pytest.mark.asyncio
    async def test_all_toggles_roundtrip(
        self, async_client: AsyncClient
    ) -> None:
        """Setting all toggles true and back to false works correctly."""
        # All true
        response = await async_client.put(
            "/api/v1/settings",
            json={
                "group_enabled": True,
                "schedule_enabled": True,
                "share_enabled": True,
                "source_group_schedules_enabled": True,
            },
        )
        if response.status_code == 401:
            pytest.skip("API key required in this environment")
        data = response.json()
        assert data["group_enabled"] is True
        assert data["schedule_enabled"] is True
        assert data["share_enabled"] is True
        assert data["source_group_schedules_enabled"] is True

        # All false
        response2 = await async_client.put(
            "/api/v1/settings",
            json={
                "group_enabled": False,
                "schedule_enabled": False,
                "share_enabled": False,
                "source_group_schedules_enabled": False,
            },
        )
        data2 = response2.json()
        assert data2["group_enabled"] is False
        assert data2["schedule_enabled"] is False
        assert data2["share_enabled"] is False
        assert data2["source_group_schedules_enabled"] is False


class TestCascadeEnforcement:
    @pytest.mark.asyncio
    async def test_put_group_off_cascades_schedule_off(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """PUT group_enabled=false auto-cascades schedule_enabled and source_group_schedules_enabled to false."""
        test_session.add(AppSettings(
            group_enabled=True, schedule_enabled=True,
            source_group_schedules_enabled=True, share_enabled=True
        ))
        await test_session.commit()

        response = await async_client.put(
            "/api/v1/settings",
            json={"group_enabled": False},
        )
        if response.status_code == 401:
            pytest.skip("API key required")
        data = response.json()
        assert data["group_enabled"] is False
        assert data["schedule_enabled"] is False, "Cascade: schedule should be forced OFF"
        assert data["source_group_schedules_enabled"] is False, "Cascade: sgs should be forced OFF"
        assert data["share_enabled"] is True, "Share is independent — should not be affected"

    @pytest.mark.asyncio
    async def test_put_group_on_does_not_cascade(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """PUT group_enabled=true does NOT force any other values."""
        test_session.add(AppSettings(
            group_enabled=False, schedule_enabled=False,
            source_group_schedules_enabled=False, share_enabled=True
        ))
        await test_session.commit()

        response = await async_client.put(
            "/api/v1/settings",
            json={"group_enabled": True},
        )
        if response.status_code == 401:
            pytest.skip("API key required")
        data = response.json()
        assert data["group_enabled"] is True
        assert data["schedule_enabled"] is False
        assert data["source_group_schedules_enabled"] is False
        assert data["share_enabled"] is True

    @pytest.mark.asyncio
    async def test_put_group_off_explicit_schedule_not_overridden(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """If group_enabled=false AND schedule_enabled=true in payload, cascade still forces schedule=false."""
        test_session.add(AppSettings(group_enabled=True, schedule_enabled=True))
        await test_session.commit()

        response = await async_client.put(
            "/api/v1/settings",
            json={"group_enabled": False, "schedule_enabled": True},
        )
        if response.status_code == 401:
            pytest.skip("API key required")
        data = response.json()
        assert data["group_enabled"] is False
        assert data["schedule_enabled"] is False, "Cascade overrides even explicit true"

    @pytest.mark.asyncio
    async def test_get_after_cascade_returns_consistent_state(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """GET after cascade PUT returns the cascaded state."""
        test_session.add(AppSettings(
            group_enabled=True, schedule_enabled=True,
            source_group_schedules_enabled=True
        ))
        await test_session.commit()

        await async_client.put("/api/v1/settings", json={"group_enabled": False})

        response = await async_client.get("/api/v1/settings")
        if response.status_code == 401:
            pytest.skip("API key required")
        data = response.json()
        assert data["group_enabled"] is False
        assert data["schedule_enabled"] is False
        assert data["source_group_schedules_enabled"] is False
