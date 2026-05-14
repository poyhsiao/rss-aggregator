"""Tests for AppSettings model."""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.app_settings import AppSettings


@pytest.mark.asyncio
async def test_app_settings_defaults_to_false(db_session: AsyncSession):
    """AppSettings fields default to False."""
    settings = AppSettings()
    db_session.add(settings)
    await db_session.commit()

    assert settings.group_enabled is False
    assert settings.schedule_enabled is False
    assert settings.share_enabled is False


@pytest.mark.asyncio
async def test_app_settings_can_update_fields(db_session: AsyncSession):
    """AppSettings fields can be updated."""
    settings = AppSettings()
    db_session.add(settings)
    await db_session.commit()

    settings.group_enabled = True
    settings.schedule_enabled = True
    await db_session.commit()

    result = await db_session.execute(select(AppSettings))
    saved = result.scalars().first()
    assert saved.group_enabled is True
    assert saved.schedule_enabled is True
    assert saved.share_enabled is False
