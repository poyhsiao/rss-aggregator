"""Service for fetching and parsing RSS feeds."""

import asyncio
import json
from datetime import datetime
from typing import Any
from urllib.parse import parse_qs, urlparse

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models import FeedItem, FetchBatch, FetchLog, Source
from src.services.stats_service import StatsService
from src.utils.time import now


class FetchService:
    """Service for fetching and parsing RSS feeds."""

    GOOGLE_URL_PREFIX = "https://www.google.com/url"

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service with a database session.

        Args:
            session: AsyncSession for database operations.
        """
        self.session = session
        self.stats_service = StatsService(session)
        self.timeout = settings.fetch_timeout
        self.retry_count = settings.fetch_retry_count
        self.retry_delay = settings.fetch_retry_delay

    def _clean_google_url(self, url: str) -> str:
        """Extract real URL from Google redirect URL.

        Args:
            url: Potential Google redirect URL.

        Returns:
            Clean URL if Google redirect, otherwise original URL.
        """
        if not url.startswith(self.GOOGLE_URL_PREFIX):
            return url

        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            real_urls = params.get("url", [])
            return real_urls[0] if real_urls else url
        except (ValueError, KeyError, IndexError):
            return url

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
            raw_link = entry.get("link", "")
            clean_link: str
            if isinstance(raw_link, str):
                clean_link = self._clean_google_url(raw_link)
            else:
                clean_link = ""

            raw_title = entry.get("title", "")
            title: str = raw_title if isinstance(raw_title, str) else ""

            raw_summary = entry.get("summary") or entry.get("description")
            description: str | None
            if isinstance(raw_summary, str):
                description = raw_summary
            else:
                description = None

            item: dict[str, Any] = {
                "title": title,
                "link": clean_link,
                "description": description,
            }

            published_at: datetime | None = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    time_tuple = entry.published_parsed[:6]
                    if all(isinstance(x, int) for x in time_tuple):
                        published_at = datetime(*time_tuple)  # type: ignore[arg-type]
                except (TypeError, ValueError, IndexError):
                    published_at = None
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                try:
                    time_tuple = entry.updated_parsed[:6]
                    if all(isinstance(x, int) for x in time_tuple):
                        published_at = datetime(*time_tuple)  # type: ignore[arg-type]
                except (TypeError, ValueError, IndexError):
                    published_at = None

            item["published_at"] = published_at
            items.append(item)

        return items

    async def fetch_source(self, source: Source, batch_id: int | None = None) -> list[FeedItem]:
        """Fetch and store RSS feed for a source.

        Args:
            source: Source to fetch.
            batch_id: Optional batch ID to associate items with.

        Returns:
            List of stored FeedItem objects.
        """
        content = await self._fetch_with_retry(source.id, source.url)

        if content is None:
            await self._log_error(source.id, f"Failed to fetch {source.url}")
            source.last_error = "Fetch failed"
            await self.stats_service.increment_stats(successful=False)
            await self.session.flush()
            return []

        items = self.parse_rss(content)
        stored_items = []

        old_items = await self.session.execute(
            select(FeedItem).where(FeedItem.source_id == source.id)
        )
        for old_item in old_items.scalars().all():
            old_item.soft_delete()

        await self.session.flush()

        for item_data in items[: settings.max_feed_items]:
            feed_item = FeedItem(
                source_id=source.id,
                batch_id=batch_id,
                title=item_data["title"],
                link=item_data["link"],
                description=item_data["description"],
                published_at=item_data["published_at"],
                fetched_at=now(),
            )
            self.session.add(feed_item)
            stored_items.append(feed_item)

        source.last_fetched_at = now()
        source.last_error = None

        await self._log_success(source.id, len(stored_items))
        await self.stats_service.increment_stats(successful=True)
        return stored_items

    async def _fetch_with_retry(self, source_id: int | None, url: str) -> str | None:
        """Fetch URL with retry logic."""
        for attempt in range(self.retry_count):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.text
            except httpx.HTTPError:
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    return None
        return None

    async def _log_error(self, source_id: int | None, error_message: str) -> None:
        """Log fetch error.

        Args:
            source_id: Source ID.
            error_message: Error message.
        """
        log = FetchLog(
            source_id=source_id,
            status="error",
            log_type="FetchError",
            message=error_message,
        )
        self.session.add(log)
        await self.session.flush()

    async def _log_success(self, source_id: int, items_count: int) -> None:
        """Log fetch success.

        Args:
            source_id: Source ID.
            items_count: Number of items fetched.
        """
        log = FetchLog(
            source_id=source_id,
            status="success",
            log_type="FetchSuccess",
            message=f"Successfully fetched {items_count} items",
            items_count=items_count,
        )
        self.session.add(log)
        await self.session.flush()

    async def fetch_all(self) -> tuple[int, dict[int, list[FeedItem]]]:
        """Fetch all active sources that need updating.

        Creates a FetchBatch record and associates all fetched items with it.

        Returns:
            Tuple of (batch_id, dict mapping source_id to list of fetched items).
        """
        result = await self.session.execute(
            select(Source).where(
                Source.is_active == True,  # noqa: E712
                Source.deleted_at.is_(None),
            )
        )
        sources = list(result.scalars().all())

        batch = FetchBatch(items_count=0, sources="")
        self.session.add(batch)
        await self.session.flush()

        results: dict[int, list[FeedItem]] = {}
        source_names: list[str] = []
        total_items = 0

        for source in sources:
            items = await self.fetch_source(source, batch_id=batch.id)
            results[source.id] = items
            if items:
                source_names.append(source.name)
                total_items += len(items)

        batch.items_count = total_items
        batch.sources = json.dumps(source_names, ensure_ascii=False)

        await self.session.commit()
        return batch.id, results