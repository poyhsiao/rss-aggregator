"""Tests for SourceGroupService."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.source_group_service import SourceGroupService
from src.services.source_service import SourceService


@pytest_asyncio.fixture
async def group_service(db_session: AsyncSession) -> SourceGroupService:
    """Create SourceGroupService instance."""
    return SourceGroupService(db_session)


@pytest_asyncio.fixture
async def source_svc(db_session: AsyncSession) -> SourceService:
    """Create SourceService instance."""
    return SourceService(db_session)


@pytest.mark.asyncio
async def test_create_group(group_service: SourceGroupService):
    """Test creating a new group."""
    group = await group_service.create_group(name="Tech")
    assert group.id is not None
    assert group.name == "Tech"


@pytest.mark.asyncio
async def test_create_duplicate_group_raises(group_service: SourceGroupService):
    """Test that creating a duplicate group raises ValueError."""
    await group_service.create_group(name="Tech")
    with pytest.raises(ValueError, match="already exists"):
        await group_service.create_group(name="Tech")


@pytest.mark.asyncio
async def test_list_groups(group_service: SourceGroupService):
    """Test listing all groups."""
    await group_service.create_group(name="A")
    await group_service.create_group(name="B")
    groups = await group_service.list_groups()
    assert len(groups) == 2


@pytest.mark.asyncio
async def test_update_group_name(group_service: SourceGroupService):
    """Test updating a group name."""
    group = await group_service.create_group(name="Old")
    updated = await group_service.update_group(group.id, name="New")
    assert updated.name == "New"


@pytest.mark.asyncio
async def test_delete_group(group_service: SourceGroupService):
    """Test deleting a group."""
    group = await group_service.create_group(name="ToDelete")
    await group_service.delete_group(group.id)
    groups = await group_service.list_groups()
    assert len(groups) == 0


@pytest.mark.asyncio
async def test_add_source_to_group(
    group_service: SourceGroupService, source_svc: SourceService
):
    """Test adding a source to a group."""
    group = await group_service.create_group(name="Tech")
    source = await source_svc.create_source("Feed", "https://example.com/rss")
    await group_service.add_source_to_group(group.id, source.id)
    groups = await group_service.get_source_groups(source.id)
    assert len(groups) == 1
    assert groups[0].id == group.id


@pytest.mark.asyncio
async def test_add_source_to_multiple_groups(
    group_service: SourceGroupService, source_svc: SourceService
):
    """Test adding a source to multiple groups."""
    g1 = await group_service.create_group(name="Tech")
    g2 = await group_service.create_group(name="News")
    source = await source_svc.create_source("Feed", "https://example.com/rss")
    await group_service.add_source_to_group(g1.id, source.id)
    await group_service.add_source_to_group(g2.id, source.id)
    groups = await group_service.get_source_groups(source.id)
    assert len(groups) == 2


@pytest.mark.asyncio
async def test_remove_source_from_group(
    group_service: SourceGroupService, source_svc: SourceService
):
    """Test removing a source from a group."""
    group = await group_service.create_group(name="Tech")
    source = await source_svc.create_source("Feed", "https://example.com/rss")
    await group_service.add_source_to_group(group.id, source.id)
    await group_service.remove_source_from_group(group.id, source.id)
    groups = await group_service.get_source_groups(source.id)
    assert len(groups) == 0


@pytest.mark.asyncio
async def test_get_group_sources(
    group_service: SourceGroupService, source_svc: SourceService
):
    """Test getting all sources in a group."""
    group = await group_service.create_group(name="Tech")
    s1 = await source_svc.create_source("Feed1", "https://example.com/1.xml")
    s2 = await source_svc.create_source("Feed2", "https://example.com/2.xml")
    await group_service.add_source_to_group(group.id, s1.id)
    await group_service.add_source_to_group(group.id, s2.id)
    sources = await group_service.get_group_sources(group.id)
    assert len(sources) == 2


@pytest.mark.asyncio
async def test_get_group_with_member_count(
    group_service: SourceGroupService, source_svc: SourceService
):
    """Test listing groups with member count."""
    group = await group_service.create_group(name="Tech")
    source = await source_svc.create_source("Feed", "https://example.com/rss")
    await group_service.add_source_to_group(group.id, source.id)
    groups = await group_service.list_groups_with_count()
    tech_group = [g for g in groups if g["name"] == "Tech"][0]
    assert tech_group["member_count"] == 1


# ==================== Error Path Tests ====================


@pytest.mark.asyncio
async def test_update_nonexistent_group_raises(group_service: SourceGroupService):
    """Test updating a non-existent group raises ValueError."""
    with pytest.raises(ValueError, match="not found"):
        await group_service.update_group(9999, name="New")


@pytest.mark.asyncio
async def test_delete_nonexistent_group_raises(group_service: SourceGroupService):
    """Test deleting a non-existent group raises ValueError."""
    with pytest.raises(ValueError, match="not found"):
        await group_service.delete_group(9999)


@pytest.mark.asyncio
async def test_add_source_to_nonexistent_group_raises(
    group_service: SourceGroupService, source_svc: SourceService
):
    """Test adding source to non-existent group raises ValueError."""
    source = await source_svc.create_source("Feed", "https://example.com/rss")
    with pytest.raises(ValueError, match="Group.*not found"):
        await group_service.add_source_to_group(9999, source.id)


@pytest.mark.asyncio
async def test_add_nonexistent_source_to_group_raises(
    group_service: SourceGroupService,
):
    """Test adding non-existent source to group raises ValueError."""
    group = await group_service.create_group(name="Tech")
    with pytest.raises(ValueError, match="Source.*not found"):
        await group_service.add_source_to_group(group.id, 9999)


@pytest.mark.asyncio
async def test_add_duplicate_membership_raises(
    group_service: SourceGroupService, source_svc: SourceService
):
    """Test adding same source to same group twice raises ValueError."""
    group = await group_service.create_group(name="Tech")
    source = await source_svc.create_source("Feed", "https://example.com/rss")
    await group_service.add_source_to_group(group.id, source.id)
    with pytest.raises(ValueError, match="already in group"):
        await group_service.add_source_to_group(group.id, source.id)


@pytest.mark.asyncio
async def test_add_deleted_source_to_group_raises(
    group_service: SourceGroupService, source_svc: SourceService, db_session
):
    """Test adding soft-deleted source to group raises ValueError."""
    group = await group_service.create_group(name="Tech")
    source = await source_svc.create_source("Feed", "https://example.com/rss")
    await source_svc.delete_source(source.id)
    with pytest.raises(ValueError, match="Source.*not found"):
        await group_service.add_source_to_group(group.id, source.id)


@pytest.mark.asyncio
async def test_remove_nonexistent_membership_raises(
    group_service: SourceGroupService, source_svc: SourceService
):
    """Test removing non-existent membership raises ValueError."""
    group = await group_service.create_group(name="Tech")
    source = await source_svc.create_source("Feed", "https://example.com/rss")
    with pytest.raises(ValueError, match="not in group"):
        await group_service.remove_source_from_group(group.id, source.id)
