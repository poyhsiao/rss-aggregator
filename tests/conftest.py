"""Pytest configuration and fixtures."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import async_session_factory, engine
from src.models import Base
from src.models.app_settings import AppSettings


@pytest.fixture
def anyio_backend():
    """Use asyncio as the async backend."""
    return "asyncio"


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def app_settings_default(db_session: AsyncSession) -> AppSettings:
    """Seed default AppSettings record."""
    settings = AppSettings()
    db_session.add(settings)
    await db_session.commit()
    await db_session.refresh(settings)
    return settings