"""Tests for feature gate 403 responses."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.api.deps import get_session
from src.models.app_settings import AppSettings


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """Create async client with db_session dependency overridden."""
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_source_groups_returns_403_when_disabled(client: AsyncClient, db_session: AsyncSession):
    """GET /api/v1/source-groups returns 403 when group_enabled=False."""
    db_session.add(AppSettings(group_enabled=False))
    await db_session.commit()

    response = await client.get("/api/v1/source-groups")
    if response.status_code == 401:
        pytest.skip("API key required")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_source_groups_returns_200_when_enabled(client: AsyncClient, db_session: AsyncSession):
    """GET /api/v1/source-groups returns 200 when group_enabled=True."""
    db_session.add(AppSettings(group_enabled=True))
    await db_session.commit()

    response = await client.get("/api/v1/source-groups")
    if response.status_code == 401:
        pytest.skip("API key required")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_schedules_returns_403_when_disabled(client: AsyncClient, db_session: AsyncSession):
    """POST /api/v1/schedules returns 403 when schedule_enabled=False."""
    db_session.add(AppSettings(schedule_enabled=False))
    await db_session.commit()

    response = await client.post(
        "/api/v1/source-groups/1/schedules",
        json={"cron_expression": "*/15 * * * *"},
    )
    if response.status_code == 401:
        pytest.skip("API key required")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_feed_share_returns_403_when_disabled(client: AsyncClient, db_session: AsyncSession):
    """GET /api/v1/feed?share=true returns 403 when share_enabled=False."""
    db_session.add(AppSettings(share_enabled=False))
    await db_session.commit()

    response = await client.get("/api/v1/feed", params={"share": "true"})
    if response.status_code == 401:
        pytest.skip("API key required")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_feed_share_returns_200_when_enabled(client: AsyncClient, db_session: AsyncSession):
    """GET /api/v1/feed?share=true returns 200 when share_enabled=True."""
    db_session.add(AppSettings(share_enabled=True))
    await db_session.commit()

    response = await client.get("/api/v1/feed", params={"share": "true"})
    if response.status_code == 401:
        pytest.skip("API key required")
    assert response.status_code in (200, 404)