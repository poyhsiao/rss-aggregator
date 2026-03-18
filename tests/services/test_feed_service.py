"""Tests for FeedService."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Source, FeedItem
from src.services.feed_service import FeedService


@pytest_asyncio.fixture
async def feed_service(db_session: AsyncSession) -> FeedService:
    """Create FeedService instance."""
    return FeedService(db_session)


@pytest_asyncio.fixture
async def sample_data(db_session: AsyncSession):
    """Create sample sources and feed items."""
    source1 = Source(name="Tech News", url="https://tech.com/feed.xml")
    source2 = Source(name="World News", url="https://world.com/feed.xml")
    db_session.add_all([source1, source2])
    await db_session.flush()

    now = datetime.utcnow()
    items = [
        FeedItem(
            source_id=source1.id,
            title="Python 3.13 Released",
            link="https://tech.com/python-3.13",
            description="New Python version",
            published_at=now - timedelta(hours=1),
        ),
        FeedItem(
            source_id=source1.id,
            title="AI Breakthrough",
            link="https://tech.com/ai",
            description="AI news",
            published_at=now - timedelta(hours=2),
        ),
        FeedItem(
            source_id=source2.id,
            title="Election Results",
            link="https://world.com/election",
            description="World news",
            published_at=now - timedelta(hours=3),
        ),
    ]
    db_session.add_all(items)
    await db_session.commit()
    return {"sources": [source1, source2], "items": items}


@pytest.mark.asyncio
async def test_get_aggregated_feed_returns_rss_xml(
    feed_service: FeedService, sample_data
):
    """Test that get_aggregated_feed returns valid RSS XML."""
    rss_xml = await feed_service.get_aggregated_feed()

    assert "<?xml version=" in rss_xml
    assert "<rss version=" in rss_xml
    assert "<channel>" in rss_xml
    assert "</channel>" in rss_xml
    assert "</rss>" in rss_xml


@pytest.mark.asyncio
async def test_get_aggregated_feed_includes_all_items(
    feed_service: FeedService, sample_data
):
    """Test that feed includes all items."""
    rss_xml = await feed_service.get_aggregated_feed()

    assert "Python 3.13 Released" in rss_xml
    assert "AI Breakthrough" in rss_xml
    assert "Election Results" in rss_xml


@pytest.mark.asyncio
async def test_get_aggregated_feed_filters_by_time(
    feed_service: FeedService, sample_data
):
    """Test that valid_time filters items correctly."""
    rss_xml = await feed_service.get_aggregated_feed(valid_time=3)

    assert "Python 3.13 Released" in rss_xml
    assert "AI Breakthrough" in rss_xml
    assert "Election Results" not in rss_xml


@pytest.mark.asyncio
async def test_get_aggregated_feed_filters_by_keywords(
    feed_service: FeedService, sample_data
):
    """Test that keywords filter items correctly."""
    rss_xml = await feed_service.get_aggregated_feed(keywords="Python;AI")

    assert "Python 3.13 Released" in rss_xml
    assert "AI Breakthrough" in rss_xml
    assert "Election Results" not in rss_xml


@pytest.mark.asyncio
async def test_get_aggregated_feed_sorts_by_published_at(
    feed_service: FeedService, sample_data
):
    """Test sorting by published_at."""
    rss_xml = await feed_service.get_aggregated_feed(
        sort_by="published_at",
        sort_order="desc",
    )

    # Newest first
    python_pos = rss_xml.find("Python 3.13 Released")
    election_pos = rss_xml.find("Election Results")
    assert python_pos < election_pos


@pytest.mark.asyncio
async def test_get_aggregated_feed_sorts_by_source(
    feed_service: FeedService, sample_data
):
    """Test sorting by source name."""
    rss_xml = await feed_service.get_aggregated_feed(
        sort_by="source",
        sort_order="asc",
    )

    # Tech News before World News
    python_pos = rss_xml.find("Python 3.13 Released")
    election_pos = rss_xml.find("Election Results")
    assert python_pos < election_pos


@pytest.mark.asyncio
async def test_get_aggregated_feed_deduplicates_by_link(
    db_session: AsyncSession, feed_service: FeedService
):
    """Test that duplicate links are removed."""
    source1 = Source(name="Source 1", url="https://s1.com/feed.xml")
    source2 = Source(name="Source 2", url="https://s2.com/feed.xml")
    db_session.add_all([source1, source2])
    await db_session.flush()

    now = datetime.utcnow()
    duplicate_link = "https://example.com/same-article"

    items = [
        FeedItem(
            source_id=source1.id,
            title="Article from Source 1",
            link=duplicate_link,
            description="Content",
            published_at=now - timedelta(hours=1),
        ),
        FeedItem(
            source_id=source2.id,
            title="Same Article from Source 2",
            link=duplicate_link,
            description="Same Content",
            published_at=now - timedelta(hours=2),
        ),
        FeedItem(
            source_id=source1.id,
            title="Unique Article",
            link="https://example.com/unique",
            description="Unique",
            published_at=now - timedelta(hours=3),
        ),
    ]
    db_session.add_all(items)
    await db_session.commit()

    rss_xml = await feed_service.get_aggregated_feed()

    assert rss_xml.count(duplicate_link) == 1
    assert "Article from Source 1" in rss_xml or "Same Article from Source 2" in rss_xml
    assert "Unique Article" in rss_xml