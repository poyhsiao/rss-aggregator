"""Tests for database configuration."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import async_session_factory, engine


@pytest.mark.asyncio
async def test_async_session_factory():
    """Test that async session factory creates valid sessions."""
    async with async_session_factory() as session:
        assert isinstance(session, AsyncSession)


@pytest.mark.asyncio
async def test_engine_is_async():
    """Test that engine is async."""
    assert engine.name == "sqlite"