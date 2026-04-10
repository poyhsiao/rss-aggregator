"""Tests for FetchBatch creation during scheduled fetches.

TDD RED-GREEN cycle:
1. RED: These tests should FAIL initially because _check_and_fetch() doesn't create FetchBatch
2. GREEN: After fixing scheduler, tests should PASS
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import FeedItem, FetchBatch, Source, SourceGroup, SourceGroupMember, SourceGroupSchedule
from src.scheduler.fetch_scheduler import FetchScheduler
from src.db.database import async_session_factory


# Mock RSS content for testing
MOCK_RSS_CONTENT = """<?xml version="1.0"?>
<rss version="2.0">
    <channel>
        <title>Test Feed</title>
        <item>
            <title>Test Item 1</title>
            <link>https://example.com/item1</link>
            <description>Description 1</description>
        </item>
        <item>
            <title>Test Item 2</title>
            <link>https://example.com/item2</link>
        </item>
    </channel>
</rss>
"""


@pytest_asyncio.fixture
async def scheduler():
    """Create FetchScheduler instance with real session factory."""
    return FetchScheduler(async_session_factory, check_interval=60)


@pytest_asyncio.fixture
async def test_source(db_session: AsyncSession) -> Source:
    """Create a test source that needs fetching."""
    source = Source(
        name="Test Feed",
        url="https://example.com/feed.xml",
        is_active=True,
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)
    return source


@pytest_asyncio.fixture
async def test_source_never_fetched(db_session: AsyncSession) -> Source:
    """Create a test source that has never been fetched."""
    source = Source(
        name="Never Fetched",
        url="https://example.com/never-fetched.xml",
        is_active=True,
        last_fetched_at=None,
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)
    return source


class TestFetchSchedulerBatchCreation:
    """Tests for FetchBatch creation in scheduler methods."""

    @pytest.mark.asyncio
    async def test_check_and_fetch_creates_fetch_batch(
        self, db_session: AsyncSession, scheduler: FetchScheduler, test_source_with_schedule: Source
    ):
        """Test that _check_and_fetch creates a FetchBatch record.

        RED: This test should FAIL because _check_and_fetch() doesn't create FetchBatch.
        GREEN: After fixing _check_and_fetch() to create FetchBatch.
        """
        # Mock HTTP response
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.text = MOCK_RSS_CONTENT
            mock_response.raise_for_status = AsyncMock()
            mock_get.return_value = mock_response

            # Execute scheduler check
            await scheduler._check_and_fetch()

        # Verify FetchBatch was created
        result = await db_session.execute(select(FetchBatch))
        batches = list(result.scalars().all())

        assert len(batches) >= 1, (
            "FetchBatch should be created during scheduled fetch. "
            "Current _check_and_fetch() implementation doesn't create FetchBatch."
        )

    @pytest.mark.asyncio
    async def test_check_and_fetch_associates_feed_items_with_batch(
        self, db_session: AsyncSession, scheduler: FetchScheduler, test_source_with_schedule: Source
    ):
        """Test that FeedItems are associated with FetchBatch during scheduled fetch.

        RED: This test should FAIL because _check_and_fetch() doesn't pass batch_id.
        GREEN: After fixing _check_and_fetch() to pass batch_id to fetch_source().
        """
        # Mock HTTP response
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.text = MOCK_RSS_CONTENT
            mock_response.raise_for_status = AsyncMock()
            mock_get.return_value = mock_response

            # Execute scheduler check
            await scheduler._check_and_fetch()

        # Verify FeedItems are associated with batch
        result = await db_session.execute(
            select(FeedItem).where(FeedItem.source_id == test_source_with_schedule.id)
        )
        items = list(result.scalars().all())

        assert len(items) >= 1, "FeedItems should be created"

        # All items should have batch_id
        for item in items:
            assert item.batch_id is not None, (
                "FeedItem should have batch_id. "
                "Current _check_and_fetch() doesn't pass batch_id to fetch_source()."
            )

    @pytest.mark.asyncio
    async def test_check_and_fetch_updates_batch_items_count(
        self, db_session: AsyncSession, scheduler: FetchScheduler, test_source_with_schedule: Source
    ):
        """Test that FetchBatch.items_count is updated correctly."""
        # Mock HTTP response
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.text = MOCK_RSS_CONTENT
            mock_response.raise_for_status = AsyncMock()
            mock_get.return_value = mock_response

            # Execute scheduler check
            await scheduler._check_and_fetch()

        # Verify batch has correct items_count
        result = await db_session.execute(select(FetchBatch))
        batches = list(result.scalars().all())

        assert len(batches) >= 1
        batch = batches[0]
        assert batch.items_count >= 1, "FetchBatch should have items_count > 0"

    @pytest.mark.asyncio
    async def test_check_and_fetch_updates_batch_sources(
        self, db_session: AsyncSession, scheduler: FetchScheduler, test_source_with_schedule: Source
    ):
        """Test that FetchBatch.sources is updated with source names."""
        # Mock HTTP response
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.text = MOCK_RSS_CONTENT
            mock_response.raise_for_status = AsyncMock()
            mock_get.return_value = mock_response

            # Execute scheduler check
            await scheduler._check_and_fetch()

        # Verify batch has sources
        result = await db_session.execute(select(FetchBatch))
        batches = list(result.scalars().all())

        assert len(batches) >= 1
        batch = batches[0]

        # sources should be a JSON array of source names
        sources_list = json.loads(batch.sources)
        assert test_source_with_schedule.name in sources_list

    @pytest.mark.asyncio
    async def test_refresh_all_creates_fetch_batch(
        self, db_session: AsyncSession, test_source: Source
    ):
        """Test that refresh_all creates FetchBatch (this should already PASS)."""
        scheduler = FetchScheduler(async_session_factory, check_interval=60)

        # Mock HTTP response
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.text = MOCK_RSS_CONTENT
            mock_response.raise_for_status = AsyncMock()
            mock_get.return_value = mock_response

            # Execute refresh_all
            await scheduler.refresh_all()

        # Verify FetchBatch was created (this should already work)
        result = await db_session.execute(select(FetchBatch))
        batches = list(result.scalars().all())

        assert len(batches) >= 1, "FetchBatch should be created during refresh_all"

    @pytest.mark.asyncio
    async def test_refresh_source_creates_fetch_batch(
        self, db_session: AsyncSession, test_source: Source
    ):
        """Test that refresh_source creates FetchBatch for tracking fetch history.

        This is expected behavior - refresh_source creates a batch to track
        all feed items fetched during the manual refresh.
        """
        scheduler = FetchScheduler(async_session_factory, check_interval=60)

        # Mock HTTP response
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.text = MOCK_RSS_CONTENT
            mock_response.raise_for_status = AsyncMock()
            mock_get.return_value = mock_response

            # Execute refresh_source
            await scheduler.refresh_source(test_source.id)

        # Verify FetchBatch was created
        result = await db_session.execute(select(FetchBatch))
        batches = list(result.scalars().all())

        assert len(batches) >= 1, "refresh_source should create FetchBatch for history tracking"

        # Verify batch has correct data
        batch = batches[0]
        assert batch.items_count >= 1, "FetchBatch should have items_count > 0"

        # Verify sources contains the source name
        sources_list = json.loads(batch.sources)
        assert test_source.name in sources_list


@pytest_asyncio.fixture
async def test_source_with_schedule(db_session: AsyncSession) -> Source:
    """Create a test source that belongs to a group with an enabled schedule."""
    source = Source(
        name="Scheduled Feed",
        url="https://example.com/scheduled-feed.xml",
        is_active=True,
        last_fetched_at=None,
    )
    db_session.add(source)
    await db_session.flush()

    group = SourceGroup(name="Test Group")
    db_session.add(group)
    await db_session.flush()

    member = SourceGroupMember(source_id=source.id, group_id=group.id)
    db_session.add(member)

    schedule = SourceGroupSchedule(
        group_id=group.id,
        cron_expression="*/30 * * * *",
        is_enabled=True,
    )
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(source)
    return source


class TestFetchSchedulerGroupScheduleFilter:
    """Tests verifying _check_and_fetch respects SourceGroupSchedule filtering."""

    @pytest.mark.asyncio
    async def test_check_and_fetch_respects_group_schedule_filter(
        self,
        db_session: AsyncSession,
        scheduler: FetchScheduler,
        test_source_with_schedule: Source,
    ):
        """Test that _check_and_fetch fetches sources whose group has an enabled schedule."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.text = MOCK_RSS_CONTENT
            mock_response.raise_for_status = AsyncMock()
            mock_get.return_value = mock_response

            await scheduler._check_and_fetch()

        result = await db_session.execute(select(FetchBatch))
        batches = list(result.scalars().all())

        assert len(batches) >= 1, (
            "FetchBatch should be created when source belongs to a group with enabled schedule."
        )
        batch = batches[0]
        assert batch.items_count >= 1, "FetchBatch should have items_count > 0"

    @pytest.mark.asyncio
    async def test_check_and_fetch_skips_source_without_group_schedule(
        self,
        db_session: AsyncSession,
        scheduler: FetchScheduler,
        test_source_never_fetched: Source,
    ):
        """Test that _check_and_fetch does NOT fetch sources with no group schedule."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.text = MOCK_RSS_CONTENT
            mock_response.raise_for_status = AsyncMock()
            mock_get.return_value = mock_response

            await scheduler._check_and_fetch()

        result = await db_session.execute(select(FetchBatch))
        batches = list(result.scalars().all())

        assert len(batches) == 0, (
            "FetchBatch should NOT be created when source has no group schedule."
        )