"""Tests for FetchService."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Source, FeedItem
from src.services.fetch_service import FetchService


@pytest_asyncio.fixture
async def fetch_service(db_session: AsyncSession) -> FetchService:
    """Create FetchService instance."""
    return FetchService(db_session)


@pytest_asyncio.fixture
async def test_source(db_session: AsyncSession) -> Source:
    """Create a test source."""
    source = Source(name="Test", url="https://example.com/feed.xml")
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)
    return source


@pytest.mark.asyncio
async def test_parse_rss_valid_feed(fetch_service: FetchService):
    """Test parsing valid RSS feed."""
    rss_content = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <item>
                <title>Item 1</title>
                <link>https://example.com/1</link>
                <description>Description 1</description>
            </item>
            <item>
                <title>Item 2</title>
                <link>https://example.com/2</link>
            </item>
        </channel>
    </rss>
    """

    items = fetch_service.parse_rss(rss_content)
    assert len(items) == 2
    assert items[0]["title"] == "Item 1"
    assert items[0]["link"] == "https://example.com/1"


@pytest.mark.asyncio
async def test_fetch_source_stores_items(
    fetch_service: FetchService, test_source: Source
):
    """Test that fetch_source stores feed items."""
    mock_rss = """<?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <item>
                <title>Test Item</title>
                <link>https://example.com/item</link>
            </item>
        </channel>
    </rss>
    """

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.text = mock_rss
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response

        await fetch_service.fetch_source(test_source)

    # Verify item was stored
    items = await fetch_service.session.execute(
        select(FeedItem).where(FeedItem.source_id == test_source.id)
    )
    feed_items = list(items.scalars().all())
    assert len(feed_items) == 1
    assert feed_items[0].title == "Test Item"