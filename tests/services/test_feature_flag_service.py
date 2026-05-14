"""Tests for FeatureFlagService."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.feature_flag import FeatureFlag
from src.services.feature_flag_service import FeatureFlagService


@pytest_asyncio.fixture
async def service(db_session: AsyncSession) -> FeatureFlagService:
    """Create FeatureFlagService instance."""
    return FeatureFlagService(db_session)


@pytest_asyncio.fixture
async def seed_flags(db_session: AsyncSession):
    """Seed feature flags into database."""
    flags = [
        FeatureFlag(key="groups_enabled", value="true"),
        FeatureFlag(key="group_schedules_enabled", value="true"),
        FeatureFlag(key="source_group_schedules_enabled", value="true"),
    ]
    db_session.add_all(flags)
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_all_feature_flags_default(service: FeatureFlagService):
    """取得所有 flags，包含預設值（空資料庫）"""
    result = await service.get_all()
    assert "groups_enabled" in result
    assert "group_schedules_enabled" in result
    assert "source_group_schedules_enabled" in result
    assert result["groups_enabled"] is True


@pytest.mark.asyncio
async def test_get_all_feature_flags_with_data(
    service: FeatureFlagService, seed_flags
):
    """從資料庫讀取已存在的 flags"""
    result = await service.get_all()
    assert result["groups_enabled"] is True


@pytest.mark.asyncio
async def test_update_feature_flag(
    service: FeatureFlagService, seed_flags
):
    """更新單一 flag"""
    await service.update("groups_enabled", False)
    result = await service.get_all()
    assert result["groups_enabled"] is False


@pytest.mark.asyncio
async def test_update_feature_flags_batch(
    service: FeatureFlagService, seed_flags
):
    """批量更新 flags"""
    await service.update_batch({
        "groups_enabled": False,
        "group_schedules_enabled": False,
    })
    result = await service.get_all()
    assert result["groups_enabled"] is False
    assert result["group_schedules_enabled"] is False
    assert result["source_group_schedules_enabled"] is True


@pytest.mark.asyncio
async def test_upsert_new_flag(service: FeatureFlagService):
    """不存在的 flag 自動建立"""
    await service.upsert("new_flag", True)
    result = await service.get_all()
    assert result["new_flag"] is True


@pytest.mark.asyncio
async def test_upsert_existing_flag(
    service: FeatureFlagService, seed_flags
):
    """已存在的 flag 更新"""
    await service.upsert("groups_enabled", False)
    result = await service.get_all()
    assert result["groups_enabled"] is False