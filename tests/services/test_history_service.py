"""Tests for HistoryService."""

import pytest
from datetime import date, datetime

from sqlalchemy import select
from src.models import FeedItem, FetchBatch, Source
from src.schemas.history import UpdateBatchNameRequest
from src.services.history_service import HistoryService


@pytest.fixture
def history_service(db_session):
    return HistoryService(db_session)


@pytest.mark.asyncio
async def test_get_history_returns_empty_list_when_no_items(history_service):
    items, pagination = await history_service.get_history()

    assert items == []
    assert pagination.total_items == 0
    assert pagination.total_pages == 0


@pytest.mark.asyncio
async def test_get_history_filters_by_date_range(db_session):
    source = Source(name="Test Source", url="https://example.com/feed.xml")
    db_session.add(source)
    await db_session.flush()

    old_item = FeedItem(
        source_id=source.id,
        title="Old Item",
        link="https://example.com/old",
        fetched_at=datetime(2024, 1, 10, 12, 0, 0),
    )
    new_item = FeedItem(
        source_id=source.id,
        title="New Item",
        link="https://example.com/new",
        fetched_at=datetime(2024, 1, 20, 12, 0, 0),
    )
    db_session.add_all([old_item, new_item])
    await db_session.commit()

    service = HistoryService(db_session)

    items, pagination = await service.get_history(
        start_date=date(2024, 1, 15),
        end_date=date(2024, 1, 25),
    )

    assert len(items) == 1
    assert items[0].title == "New Item"
    assert pagination.total_items == 1


class TestUpdateBatchName:
    @pytest.mark.asyncio
    async def test_update_batch_name_success(self, db_session):
        source = Source(name="Test Source", url="https://example.com/feed.xml")
        db_session.add(source)
        await db_session.flush()

        batch = FetchBatch(items_count=2, sources='["Test Source"]')
        db_session.add(batch)
        await db_session.flush()

        items = [
            FeedItem(
                source_id=source.id,
                batch_id=batch.id,
                title=f"Item {i}",
                link=f"https://example.com/{i}",
            )
            for i in range(2)
        ]
        db_session.add_all(items)
        await db_session.commit()

        service = HistoryService(db_session)
        result = await service.update_batch_name(
            batch.id,
            UpdateBatchNameRequest(name="My Custom Batch Name"),
        )

        assert result is not None
        assert result.name == "My Custom Batch Name"
        assert result.id == batch.id
        assert result.items_count == 2

    @pytest.mark.asyncio
    async def test_update_batch_name_returns_none_for_nonexistent_batch(self, history_service):
        result = await history_service.update_batch_name(
            99999,
            UpdateBatchNameRequest(name="Test Name"),
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_update_batch_name_overwrites_existing_notes(self, db_session):
        batch = FetchBatch(items_count=0, sources='[]', notes="Old Name")
        db_session.add(batch)
        await db_session.commit()

        service = HistoryService(db_session)
        result = await service.update_batch_name(
            batch.id,
            UpdateBatchNameRequest(name="New Name"),
        )

        assert result is not None
        assert result.name == "New Name"


class TestDeleteBatch:
    @pytest.mark.asyncio
    async def test_delete_batch_success(self, db_session):
        source = Source(name="Test Source", url="https://example.com/feed.xml")
        db_session.add(source)
        await db_session.flush()

        batch = FetchBatch(items_count=2, sources='["Test Source"]')
        db_session.add(batch)
        await db_session.flush()

        items = [
            FeedItem(
                source_id=source.id,
                batch_id=batch.id,
                title=f"Item {i}",
                link=f"https://example.com/{i}",
            )
            for i in range(2)
        ]
        db_session.add_all(items)
        await db_session.commit()

        batch_id = batch.id
        service = HistoryService(db_session)

        result = await service.delete_batch(batch_id)

        assert result is True

        batches_result = await service.get_history_batches()
        assert all(b.id != batch_id for b in batches_result.batches)

    @pytest.mark.asyncio
    async def test_delete_batch_returns_false_for_nonexistent_batch(self, history_service):
        result = await history_service.delete_batch(99999)

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_batch_removes_batch_from_list(self, db_session):
        batch1 = FetchBatch(items_count=1, sources='[]')
        batch2 = FetchBatch(items_count=2, sources='[]')
        db_session.add_all([batch1, batch2])
        await db_session.commit()

        service = HistoryService(db_session)

        result_before = await service.get_history_batches()
        assert len(result_before.batches) == 2

        await service.delete_batch(batch1.id)

        result_after = await service.get_history_batches()
        assert len(result_after.batches) == 1
        assert result_after.batches[0].id == batch2.id


class TestGetBatchFeedItems:
    @pytest.mark.asyncio
    async def test_get_batch_feed_items_returns_items(self, db_session):
        source = Source(name="Test Source", url="https://example.com/feed.xml")
        db_session.add(source)
        await db_session.flush()

        batch = FetchBatch(items_count=3, sources='["Test Source"]')
        db_session.add(batch)
        await db_session.flush()

        items = [
            FeedItem(
                source_id=source.id,
                batch_id=batch.id,
                title=f"Article {i}",
                link=f"https://example.com/article-{i}",
                description=f"Description {i}",
            )
            for i in range(3)
        ]
        db_session.add_all(items)
        await db_session.commit()

        service = HistoryService(db_session)
        result = await service.get_batch_feed_items(batch.id)

        assert len(result) == 3
        for item in result:
            assert item.source == "Test Source"
            assert item.title.startswith("Article")
            assert item.link.startswith("https://example.com/article-")

    @pytest.mark.asyncio
    async def test_get_batch_feed_items_returns_empty_for_empty_batch(self, db_session):
        batch = FetchBatch(items_count=0, sources='[]')
        db_session.add(batch)
        await db_session.commit()

        service = HistoryService(db_session)
        result = await service.get_batch_feed_items(batch.id)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_batch_feed_items_returns_empty_for_nonexistent_batch(self, history_service):
        result = await history_service.get_batch_feed_items(99999)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_batch_feed_items_includes_published_at(self, db_session):
        source = Source(name="Test Source", url="https://example.com/feed.xml")
        db_session.add(source)
        await db_session.flush()

        batch = FetchBatch(items_count=1, sources='["Test Source"]')
        db_session.add(batch)
        await db_session.flush()

        item = FeedItem(
            source_id=source.id,
            batch_id=batch.id,
            title="Test Article",
            link="https://example.com/article",
            published_at=datetime(2024, 1, 15, 10, 30, 0),
        )
        db_session.add(item)
        await db_session.commit()

        service = HistoryService(db_session)
        result = await service.get_batch_feed_items(batch.id)

        assert len(result) == 1
        assert result[0].published_at is not None
        assert "2024-01-15" in result[0].published_at


class TestGetBatchDisplayName:
    @pytest.mark.asyncio
    async def test_returns_notes_if_present(self, history_service):
        batch = FetchBatch(items_count=0, sources='[]', notes="My Batch")
        db_session = history_service.session
        db_session.add(batch)
        await db_session.commit()

        result = history_service._get_batch_display_name(batch)

        assert result == "My Batch"

    @pytest.mark.asyncio
    async def test_returns_formatted_created_at_if_no_notes(self, history_service):
        batch = FetchBatch(items_count=0, sources='[]')
        db_session = history_service.session
        db_session.add(batch)
        await db_session.commit()

        result = history_service._get_batch_display_name(batch)

        assert result is not None
        assert batch.id is not None

    @pytest.mark.asyncio
    async def test_returns_batch_id_fallback(self, history_service, db_session):
        batch = FetchBatch(items_count=0, sources='[]')
        db_session.add(batch)
        await db_session.commit()

        result = history_service._get_batch_display_name(batch)

        assert batch.id is not None
        assert result is not None


class TestSourceGroupsInHistory:
    @pytest.mark.asyncio
    async def test_history_includes_source_groups(self, db_session):
        from src.services.source_group_service import SourceGroupService
        from src.services.source_service import SourceService

        group_svc = SourceGroupService(db_session)
        source_svc = SourceService(db_session)

        group = await group_svc.create_group(name="Tech")
        source = await source_svc.create_source("Feed", "https://example.com/rss")
        await group_svc.add_source_to_group(group.id, source.id)

        history_svc = HistoryService(db_session)
        batches = await history_svc.get_history_batches()
        assert isinstance(batches.batches, list)

    @pytest.mark.asyncio
    async def test_history_items_contain_source_groups(self, db_session):
        from src.services.source_group_service import SourceGroupService
        from src.services.source_service import SourceService

        group_svc = SourceGroupService(db_session)
        source_svc = SourceService(db_session)

        group = await group_svc.create_group(name="Tech")
        source = await source_svc.create_source("Feed", "https://example.com/rss")
        await group_svc.add_source_to_group(group.id, source.id)

        item = FeedItem(
            source_id=source.id,
            title="Test",
            link="https://example.com/1",
            fetched_at=datetime(2024, 1, 15, 10, 0, 0),
        )
        db_session.add(item)
        await db_session.commit()

        history_svc = HistoryService(db_session)
        items, _ = await history_svc.get_history()

        assert len(items) == 1
        assert items[0].source_groups == [{"id": group.id, "name": "Tech"}]

    @pytest.mark.asyncio
    async def test_batch_feed_items_contain_source_groups(self, db_session):
        from src.services.source_group_service import SourceGroupService
        from src.services.source_service import SourceService

        group_svc = SourceGroupService(db_session)
        source_svc = SourceService(db_session)

        group = await group_svc.create_group(name="News")
        source = await source_svc.create_source("Feed", "https://example.com/rss")
        await group_svc.add_source_to_group(group.id, source.id)

        batch = FetchBatch(items_count=1, sources='["Feed"]')
        db_session.add(batch)
        await db_session.flush()

        item = FeedItem(
            source_id=source.id,
            batch_id=batch.id,
            title="Test",
            link="https://example.com/1",
        )
        db_session.add(item)
        await db_session.commit()

        history_svc = HistoryService(db_session)
        items = await history_svc.get_batch_feed_items(batch.id)

        assert len(items) == 1
        assert items[0].source_groups == [{"id": group.id, "name": "News"}]

    @pytest.mark.asyncio
    async def test_batch_groups_aggregated(self, db_session):
        from src.services.source_group_service import SourceGroupService
        from src.services.source_service import SourceService

        group_svc = SourceGroupService(db_session)
        source_svc = SourceService(db_session)

        group = await group_svc.create_group(name="Tech")
        source = await source_svc.create_source("Feed", "https://example.com/rss")
        await group_svc.add_source_to_group(group.id, source.id)

        batch = FetchBatch(items_count=1, sources='["Feed"]')
        db_session.add(batch)
        await db_session.flush()

        item = FeedItem(
            source_id=source.id,
            batch_id=batch.id,
            title="Test",
            link="https://example.com/1",
        )
        db_session.add(item)
        await db_session.commit()

        history_svc = HistoryService(db_session)
        batches_response = await history_svc.get_history_batches()

        assert len(batches_response.batches) == 1
        assert batches_response.batches[0].groups == [{"id": group.id, "name": "Tech"}]

    @pytest.mark.asyncio
    async def test_get_history_batches_filter_by_group_id(self, db_session):
        from src.services.source_group_service import SourceGroupService
        from src.services.source_service import SourceService

        group_svc = SourceGroupService(db_session)
        source_svc = SourceService(db_session)

        group1 = await group_svc.create_group(name="Tech")
        group2 = await group_svc.create_group(name="News")

        source1 = await source_svc.create_source("Tech Feed", "https://tech.com/rss")
        source2 = await source_svc.create_source("News Feed", "https://news.com/rss")

        await group_svc.add_source_to_group(group1.id, source1.id)
        await group_svc.add_source_to_group(group2.id, source2.id)

        batch1 = FetchBatch(items_count=1, sources='["Tech Feed"]')
        batch2 = FetchBatch(items_count=1, sources='["News Feed"]')
        db_session.add_all([batch1, batch2])
        await db_session.flush()

        db_session.add_all([
            FeedItem(source_id=source1.id, batch_id=batch1.id, title="Tech", link="https://tech.com/1"),
            FeedItem(source_id=source2.id, batch_id=batch2.id, title="News", link="https://news.com/1"),
        ])
        await db_session.commit()

        history_svc = HistoryService(db_session)
        batches_response = await history_svc.get_history_batches(group_id=group1.id)

        assert len(batches_response.batches) == 1
        assert batch1.id in [b.id for b in batches_response.batches]

    @pytest.mark.asyncio
    async def test_get_history_batches_filter_by_group_id_returns_empty(self, db_session):
        from src.services.source_group_service import SourceGroupService
        from src.services.source_service import SourceService

        group_svc = SourceGroupService(db_session)
        source_svc = SourceService(db_session)

        group = await group_svc.create_group(name="Tech")
        source = await source_svc.create_source("Other Feed", "https://other.com/rss")

        batch = FetchBatch(items_count=1, sources='["Other Feed"]')
        db_session.add(batch)
        await db_session.flush()

        db_session.add(FeedItem(source_id=source.id, batch_id=batch.id, title="Other", link="https://other.com/1"))
        await db_session.commit()

        history_svc = HistoryService(db_session)
        batches_response = await history_svc.get_history_batches(group_id=group.id)

        assert len(batches_response.batches) == 0


class TestDeleteAllHistory:
    @pytest.mark.asyncio
    async def test_delete_all_history_removes_all_feed_items(self, db_session):
        """Delete all history should remove all FeedItems with batch_id."""
        source = Source(name="Test Source", url="https://example.com/feed.xml")
        db_session.add(source)
        await db_session.flush()

        batch = FetchBatch(items_count=2, sources='["Test Source"]')
        db_session.add(batch)
        await db_session.flush()

        items = [
            FeedItem(source_id=source.id, batch_id=batch.id, title=f"Item {i}", link=f"https://example.com/{i}")
            for i in range(2)
        ]
        db_session.add_all(items)
        await db_session.commit()

        service = HistoryService(db_session)
        deleted_count = await service.delete_all_history()

        assert deleted_count == 2

        # Verify all FeedItems with batch_id are deleted
        items_query = await db_session.execute(
            select(FeedItem).where(FeedItem.batch_id.isnot(None))
        )
        remaining = list(items_query.scalars().all())
        assert len(remaining) == 0

    @pytest.mark.asyncio
    async def test_delete_all_history_removes_all_batches(self, db_session):
        """Delete all history should remove all FetchBatches."""
        source = Source(name="Test Source", url="https://example.com/feed.xml")
        db_session.add(source)
        await db_session.flush()

        batch = FetchBatch(items_count=1, sources='["Test Source"]')
        db_session.add(batch)
        await db_session.flush()

        db_session.add(FeedItem(source_id=source.id, batch_id=batch.id, title="Item", link="https://example.com/1"))
        await db_session.commit()

        service = HistoryService(db_session)
        await service.delete_all_history()

        # Verify all FetchBatches are deleted
        batches_query = await db_session.execute(select(FetchBatch))
        batches = list(batches_query.scalars().all())
        assert len(batches) == 0

    @pytest.mark.asyncio
    async def test_delete_all_history_returns_zero_when_empty(self, db_session):
        """Delete all history on empty database returns 0."""
        service = HistoryService(db_session)
        deleted_count = await service.delete_all_history()

        assert deleted_count == 0


class TestDeleteHistoryByGroup:
    @pytest.mark.asyncio
    async def test_delete_history_by_group_removes_only_group_items(self, db_session):
        """Delete by group should only remove FeedItems from sources in that group."""
        from src.models import SourceGroup, SourceGroupMember

        # Create two groups
        group1 = SourceGroup(name="Group 1")
        group2 = SourceGroup(name="Group 2")
        db_session.add_all([group1, group2])
        await db_session.flush()

        # Create two sources, each in different group
        source1 = Source(name="Source 1", url="https://example.com/feed1.xml")
        source2 = Source(name="Source 2", url="https://example.com/feed2.xml")
        db_session.add_all([source1, source2])
        await db_session.flush()

        # Link source1 to group1, source2 to group2
        db_session.add(SourceGroupMember(source_id=source1.id, group_id=group1.id))
        db_session.add(SourceGroupMember(source_id=source2.id, group_id=group2.id))
        await db_session.commit()

        # Create batch with items from both sources
        batch = FetchBatch(items_count=2, sources='["Source 1", "Source 2"]', groups='[{"id": 1, "name": "Group 1"}, {"id": 2, "name": "Group 2"}]')
        db_session.add(batch)
        await db_session.flush()

        item1 = FeedItem(source_id=source1.id, batch_id=batch.id, title="Item from Source 1", link="https://example.com/s1")
        item2 = FeedItem(source_id=source2.id, batch_id=batch.id, title="Item from Source 2", link="https://example.com/s2")
        db_session.add_all([item1, item2])
        await db_session.commit()

        service = HistoryService(db_session)
        deleted_count = await service.delete_history_by_group(group1.id)

        assert deleted_count == 1

        # Verify only source1's item is deleted
        item1_query = await db_session.execute(select(FeedItem).where(FeedItem.id == item1.id))
        item1_remaining = item1_query.scalar_one_or_none()
        assert item1_remaining is None

        # Verify source2's item remains
        item2_query = await db_session.execute(select(FeedItem).where(FeedItem.id == item2.id))
        item2_remaining = item2_query.scalar_one_or_none()
        assert item2_remaining is not None

    @pytest.mark.asyncio
    async def test_delete_history_by_group_returns_minus_one_for_nonexistent_group(self, db_session):
        """Delete by group should return -1 for non-existent group."""
        service = HistoryService(db_session)
        result = await service.delete_history_by_group(99999)

        assert result == -1

    @pytest.mark.asyncio
    async def test_delete_history_by_group_returns_zero_for_empty_group(self, db_session):
        """Delete by group should return 0 for group with no sources."""
        from src.models import SourceGroup

        group = SourceGroup(name="Empty Group")
        db_session.add(group)
        await db_session.commit()

        service = HistoryService(db_session)
        result = await service.delete_history_by_group(group.id)

        assert result == 0

    @pytest.mark.asyncio
    async def test_delete_history_by_group_deletes_empty_batches(self, db_session):
        """Delete by group should delete FetchBatches that become empty."""
        from src.models import SourceGroup, SourceGroupMember

        # Create group
        group = SourceGroup(name="Group Only")
        db_session.add(group)
        await db_session.flush()

        # Create source in this group only
        source = Source(name="Solo Source", url="https://example.com/feed.xml")
        db_session.add(source)
        await db_session.flush()

        db_session.add(SourceGroupMember(source_id=source.id, group_id=group.id))
        await db_session.flush()

        # Create batch with one item from this source
        batch = FetchBatch(items_count=1, sources='["Solo Source"]', groups='[{"id": 1, "name": "Group Only"}]')
        db_session.add(batch)
        await db_session.flush()

        item = FeedItem(source_id=source.id, batch_id=batch.id, title="Solo Item", link="https://example.com/solo")
        db_session.add(item)
        await db_session.commit()

        service = HistoryService(db_session)
        await service.delete_history_by_group(group.id)

        # Verify the batch is deleted because it became empty
        batch_query = await db_session.execute(select(FetchBatch).where(FetchBatch.id == batch.id))
        batch_remaining = batch_query.scalar_one_or_none()
        assert batch_remaining is None