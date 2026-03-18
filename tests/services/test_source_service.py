"""Tests for SourceService."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Source
from src.services.source_service import SourceService


@pytest_asyncio.fixture
async def source_service(db_session: AsyncSession) -> SourceService:
    """Create SourceService instance."""
    return SourceService(db_session)


@pytest.mark.asyncio
async def test_create_source(source_service: SourceService):
    """Test creating a new source."""
    source = await source_service.create_source(
        name="Test Feed", url="https://example.com/feed.xml"
    )
    assert source.id is not None
    assert source.name == "Test Feed"
    assert source.url == "https://example.com/feed.xml"
    assert source.fetch_interval == 900
    assert source.is_active is True


@pytest.mark.asyncio
async def test_create_duplicate_url_raises_error(source_service: SourceService):
    """Test that duplicate URLs raise an error."""
    await source_service.create_source(name="Feed 1", url="https://example.com/feed.xml")

    with pytest.raises(ValueError, match="already exists"):
        await source_service.create_source(name="Feed 2", url="https://example.com/feed.xml")


@pytest.mark.asyncio
async def test_get_sources(source_service: SourceService):
    """Test getting all sources."""
    await source_service.create_source(name="Feed 1", url="https://example.com/1.xml")
    await source_service.create_source(name="Feed 2", url="https://example.com/2.xml")

    sources = await source_service.get_sources()
    assert len(sources) == 2


@pytest.mark.asyncio
async def test_get_source_by_id(source_service: SourceService):
    """Test getting a source by ID."""
    created = await source_service.create_source(
        name="Test", url="https://example.com/feed.xml"
    )

    found = await source_service.get_source(created.id)
    assert found is not None
    assert found.id == created.id


@pytest.mark.asyncio
async def test_update_source(source_service: SourceService):
    """Test updating a source."""
    source = await source_service.create_source(
        name="Original", url="https://example.com/feed.xml"
    )

    updated = await source_service.update_source(
        source.id, name="Updated", fetch_interval=1800
    )
    assert updated.name == "Updated"
    assert updated.fetch_interval == 1800


@pytest.mark.asyncio
async def test_delete_source(source_service: SourceService):
    """Test soft deleting a source."""
    source = await source_service.create_source(
        name="Test", url="https://example.com/feed.xml"
    )

    await source_service.delete_source(source.id)

    deleted = await source_service.get_source(source.id)
    assert deleted is None

    all_sources = await source_service.get_sources(include_deleted=True)
    assert len(all_sources) == 1