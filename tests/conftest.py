"""Pytest configuration and fixtures."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import async_session_factory, engine
from src.models import Base


@pytest.fixture
def anyio_backend():
    """Use asyncio as the async backend."""
    return "asyncio"


@pytest.fixture
async def db_session():
    """Create a test database session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)