"""Backend E2E tests for feature settings toggle.

These tests use the real FastAPI test client with a temporary DB.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.api.deps import get_session
from src.models.app_settings import AppSettings


@pytest_asyncio.fixture
async def ac(db_session: AsyncSession):
    """Async HTTP client with DB session override."""
    app.dependency_overrides[get_session] = lambda: db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_full_toggle_cycle(ac: AsyncClient, db_session: AsyncSession):
    """Enable all features, verify 403 gates lift, disable and verify gates block."""
    # 1. Start with all off — gates should block
    db_session.add(AppSettings(group_enabled=False, schedule_enabled=False, share_enabled=False))
    await db_session.commit()

    # 2. GET settings, verify defaults
    resp = await ac.get("/api/v1/settings")
    if resp.status_code == 401:
        pytest.skip("API key required in this env")
    data = resp.json()
    assert data["group_enabled"] is False

    # 3. Enable all features
    resp = await ac.put("/api/v1/settings", json={
        "group_enabled": True,
        "schedule_enabled": True,
        "share_enabled": True,
    })
    assert resp.status_code == 200
    enabled = resp.json()
    assert enabled["group_enabled"] is True

    # 4. Verify gates lift
    resp_groups = await ac.get("/api/v1/source-groups")
    assert resp_groups.status_code == 200

    resp_feed = await ac.get("/api/v1/feed", params={"share": "true"})
    assert resp_feed.status_code in (200, 404)

    # 5. Disable group feature
    resp = await ac.put("/api/v1/settings", json={"group_enabled": False})
    assert resp.json()["group_enabled"] is False

    # 6. Verify gate blocks
    resp_groups = await ac.get("/api/v1/source-groups")
    assert resp_groups.status_code == 403


@pytest.mark.asyncio
async def test_partial_update_preserves_other_fields(ac: AsyncClient, db_session: AsyncSession):
    """PUT with only one field should not change others."""
    db_session.add(AppSettings(group_enabled=True, schedule_enabled=False, share_enabled=False))
    await db_session.commit()

    resp = await ac.put("/api/v1/settings", json={"share_enabled": True})
    if resp.status_code == 401:
        pytest.skip("API key required")

    data = resp.json()
    assert data["group_enabled"] is True     # preserved
    assert data["schedule_enabled"] is False  # preserved
    assert data["share_enabled"] is True     # changed


@pytest.mark.asyncio
async def test_schedules_gate_when_disabled(ac: AsyncClient, db_session: AsyncSession):
    """POST /api/v1/schedules returns 403 when schedule_enabled=False."""
    db_session.add(AppSettings(group_enabled=True, schedule_enabled=False))
    await db_session.commit()

    resp = await ac.post(
        "/api/v1/source-groups/1/schedules",
        json={"cron_expression": "*/15 * * * *"},
    )
    if resp.status_code == 401:
        pytest.skip("API key required")
    assert resp.status_code == 403
