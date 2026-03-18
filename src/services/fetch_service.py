"""Service for fetching and parsing RSS feeds."""

import asyncio
from datetime import datetime
from typing import Any

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models import ErrorLog, FeedItem, Source


class FetchService:
    """Service for fetching and parsing RSS feeds."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service with a database session.

        Args:
            session: AsyncSession for database operations.
        """
        self.session = session
        self.timeout = settings.fetch_timeout
        self.retry_count = settings.fetch_retry_count
        self.retry_delay = settings.fetch_retry_delay

    def parse_rss(self, content: str) -> list[dict[str, Any]]:
        """Parse RSS/Atom feed content.

        Args:
            content: RSS XML content.

        Returns:
            List of feed items with title, link, description, published_at.
        """
        feed = feedparser.parse(content)
        items = []

        for entry in feed.entries:
            item: dict[str, Any] = {
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "description": entry.get("summary") or entry.get("description"),
            }

            # Parse publication date
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                item["published_at"] = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                item["published_at"] = datetime(*entry.updated_parsed[:6])
            else:
                item["published_at"] = None

            items.append(item)

        return items

    async def fetch_source(self, source: Source) -> list[FeedItem]:
        """Fetch and store RSS feed for a source.

        Args:
            source: Source to fetch.

        Returns:
            List of stored FeedItem instances.
        """
        content = await self._fetch_with_retry(source.url)

        if content is None:
            return []

        items = self.parse_rss(content)
        stored_items = []

        # Soft delete old items
        old_items = await self.session.execute(
            select(FeedItem).where(FeedItem.source_id == source.id)
        )
        for old_item in old_items.scalars().all():
            old_item.soft_delete()

        # Store new items
        for item_data in items[: settings.max_feed_items]:
            feed_item = FeedItem(
                source_id=source.id,
                title=item_data["title"],
                link=item_data["link"],
                description=item_data["description"],
                published_at=item_data["published_at"],
            )
            self.session.add(feed_item)
            stored_items.append(feed_item)

        # Update source status
        source.last_fetched_at = datetime.utcnow()
        source.last_error = None

        await self.session.flush()
        return stored_items

    async def _fetch_with_retry(self, url: str) -> str | None:
        """Fetch URL with retry logic.

        Args:
            url: URL to fetch.

        Returns:
            Content string or None if all retries failed.
        """
        for attempt in range(self.retry_count):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.text
            except Exception as e:
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    await self._log_error(url, str(e))
                    return None
        return None

    async def _log_error(self, url: str, error_message: str) -> None:
        """Log fetch error.

        Args:
            url: URL that failed.
            error_message: Error message.
        """
        log = ErrorLog(
            error_type="FetchError",
            error_message=f"Failed to fetch {url}: {error_message}",
        )
        self.session.add(log)
        await self.session.flush()

    async def fetch_all(self) -> dict[int, list[FeedItem]]:
        """Fetch all active sources that need updating.

        Returns:
            Dict mapping source_id to list of fetched items.
        """
        # Get sources that need fetching
        result = await self.session.execute(
            select(Source).where(
                Source.is_active == True,  # noqa: E712
                Source.deleted_at.is_(None),
            )
        )
        sources = list(result.scalars().all())

        results = {}
        for source in sources:
            items = await self.fetch_source(source)
            results[source.id] = items

        return results