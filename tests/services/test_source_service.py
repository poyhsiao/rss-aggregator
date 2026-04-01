"""Tests for SourceService."""

import pytest
import pytest_asyncio
from sqlalchemy import select
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
    assert source.is_active is True


@pytest.mark.asyncio
async def test_create_duplicate_url_raises_error(source_service: SourceService):
    """Test that duplicate URLs raise an error."""
    await source_service.create_source(
        name="Feed 1", url="https://example.com/feed.xml"
    )

    with pytest.raises(ValueError, match="already exists"):
        await source_service.create_source(
            name="Feed 2", url="https://example.com/feed.xml"
        )


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
        source.id, name="Updated"
    )
    assert updated.name == "Updated"


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


# ==================== Trash Management Tests ====================


@pytest.mark.asyncio
async def test_get_trash_sources(source_service: SourceService):
    """Test getting only soft-deleted sources."""
    source = await source_service.create_source("Trash Source", "https://trash.com/rss")
    await source_service.delete_source(source.id)

    active = await source_service.create_source("Active Source", "https://active.com/rss")

    trash = await source_service.get_trash_sources()

    assert len(trash) == 1
    assert trash[0].name == "Trash Source"
    assert trash[0].deleted_at is not None


@pytest.mark.asyncio
async def test_get_trash_source(source_service: SourceService):
    """Test getting a single trash source by ID."""
    source = await source_service.create_source("To Delete", "https://delete.com/rss")
    await source_service.delete_source(source.id)

    trash = await source_service.get_trash_source(source.id)

    assert trash is not None
    assert trash.name == "To Delete"
    assert trash.deleted_at is not None

    active = await source_service.create_source("Active", "https://active2.com/rss")
    assert await source_service.get_trash_source(active.id) is None
    assert await source_service.get_trash_source(9999) is None


@pytest.mark.asyncio
async def test_check_restore_conflict_none(source_service: SourceService):
    """Test no conflict when name and URL are unique."""
    source = await source_service.create_source("Unique", "https://unique.com/rss")
    await source_service.delete_source(source.id)

    conflict = await source_service.check_restore_conflict(source.id)

    assert conflict is None


@pytest.mark.asyncio
async def test_check_restore_conflict_name(source_service: SourceService):
    """Test conflict detection for duplicate name."""
    deleted = await source_service.create_source("Same Name", "https://deleted.com/rss")
    await source_service.delete_source(deleted.id)

    await source_service.create_source("Same Name", "https://different.com/rss")

    conflict = await source_service.check_restore_conflict(deleted.id)

    assert conflict is not None
    assert conflict["conflict_type"] == "name"


@pytest.mark.asyncio
async def test_check_restore_conflict_url(source_service: SourceService):
    """Test conflict detection for duplicate URL."""
    deleted = await source_service.create_source("Deleted", "https://same-url.com/rss")
    await source_service.delete_source(deleted.id)

    await source_service.create_source("Different Name", "https://same-url.com/rss")

    conflict = await source_service.check_restore_conflict(deleted.id)

    assert conflict is not None
    assert conflict["conflict_type"] == "url"


@pytest.mark.asyncio
async def test_check_restore_conflict_both(source_service: SourceService):
    """Test conflict detection for both name and URL."""
    deleted = await source_service.create_source("Both Match", "https://both.com/rss")
    await source_service.delete_source(deleted.id)

    await source_service.create_source("Both Match", "https://both.com/rss")

    conflict = await source_service.check_restore_conflict(deleted.id)

    assert conflict is not None
    assert conflict["conflict_type"] == "both"


@pytest.mark.asyncio
async def test_restore_source_no_conflict(source_service: SourceService):
    """Test restoring without conflict."""
    source = await source_service.create_source("To Restore", "https://restore.com/rss")
    await source_service.delete_source(source.id)

    restored = await source_service.restore_source(source.id)

    assert restored.deleted_at is None
    assert restored.name == "To Restore"


@pytest.mark.asyncio
async def test_restore_source_overwrite(source_service: SourceService, db_session: AsyncSession):
    """Test restoring with overwrite."""
    deleted = await source_service.create_source("Overwrite", "https://overwrite.com/rss")
    await source_service.delete_source(deleted.id)

    existing = await source_service.create_source("Overwrite", "https://overwrite.com/rss")

    restored = await source_service.restore_source(deleted.id, overwrite=True)

    assert restored.deleted_at is None

    await db_session.refresh(existing)
    assert existing.deleted_at is not None


@pytest.mark.asyncio
async def test_restore_source_not_found(source_service: SourceService):
    """Test restoring non-existent trash item."""
    with pytest.raises(ValueError, match="not found"):
        await source_service.restore_source(9999)


@pytest.mark.asyncio
async def test_permanent_delete_source(source_service: SourceService, db_session: AsyncSession):
    """Test permanently deleting a source."""
    source = await source_service.create_source("To Perma Delete", "https://perma.com/rss")
    await source_service.delete_source(source.id)
    source_id = source.id

    await source_service.permanent_delete_source(source_id)

    result = await db_session.execute(
        select(Source).where(Source.id == source_id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_permanent_delete_source_not_in_trash(source_service: SourceService):
    """Test permanent delete fails for non-trash item."""
    source = await source_service.create_source("Active", "https://active3.com/rss")

    with pytest.raises(ValueError, match="not found"):
        await source_service.permanent_delete_source(source.id)


@pytest.mark.asyncio
async def test_clear_trash(source_service: SourceService):
    """Test clearing all trash items."""
    s1 = await source_service.create_source("Trash 1", "https://trash1.com/rss")
    s2 = await source_service.create_source("Trash 2", "https://trash2.com/rss")
    s3 = await source_service.create_source("Active", "https://active4.com/rss")

    await source_service.delete_source(s1.id)
    await source_service.delete_source(s2.id)

    count = await source_service.clear_trash()

    assert count == 2

    trash = await source_service.get_trash_sources()
    assert len(trash) == 0

    active = await source_service.get_source(s3.id)
    assert active is not None
