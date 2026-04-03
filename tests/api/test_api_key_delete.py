"""Tests for API key hard-delete behavior."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models import APIKey


@pytest.mark.asyncio
async def test_delete_key_removes_key_permanently(db_session: AsyncSession):
    """Test that deleting an API key permanently removes it."""
    api_key = APIKey(key="test-delete-key-123", name="Delete Test")
    db_session.add(api_key)
    await db_session.commit()

    result = await db_session.execute(select(APIKey).where(APIKey.key == "test-delete-key-123"))
    assert result.scalar_one_or_none() is not None

    await db_session.delete(api_key)
    await db_session.commit()

    result = await db_session.execute(select(APIKey).where(APIKey.key == "test-delete-key-123"))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_list_keys_shows_all_active_keys(db_session: AsyncSession):
    """Test that listing keys shows all keys (no soft-delete filtering)."""
    for i in range(3):
        db_session.add(APIKey(key=f"list-key-{i}", name=f"Key {i}"))
    await db_session.commit()

    result = await db_session.execute(select(APIKey))
    keys = list(result.scalars().all())
    assert len(keys) == 3
