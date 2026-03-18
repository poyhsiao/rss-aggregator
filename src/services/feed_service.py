"""Service for aggregating and filtering RSS feeds."""

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models import FeedItem, Source


class FeedService:
    """Service for aggregating RSS feeds."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service with a database session.

        Args:
            session: AsyncSession for database operations.
        """
        self.session = session

    async def get_aggregated_feed(
        self,
        sort_by: str = "published_at",
        sort_order: str = "desc",
        valid_time: int | None = None,
        keywords: str | None = None,
    ) -> str:
        """Get aggregated RSS feed.

        Args:
            sort_by: Sort field ("published_at" or "source").
            sort_order: Sort direction ("asc" or "desc").
            valid_time: Time range in hours (None = all items).
            keywords: Semicolon-separated keywords for title filtering.

        Returns:
            RSS 2.0 XML string.
        """
        items = await self._fetch_items(
            sort_by=sort_by,
            sort_order=sort_order,
            valid_time=valid_time,
            keywords=keywords,
        )
        return self._generate_rss_xml(items)

    async def _fetch_items(
        self,
        sort_by: str,
        sort_order: str,
        valid_time: int | None,
        keywords: str | None,
    ) -> list[FeedItem]:
        """Fetch filtered feed items from database."""
        query = (
            select(FeedItem)
            .options(joinedload(FeedItem.source))
            .where(
                FeedItem.deleted_at.is_(None),
                FeedItem.source.has(Source.is_active == True),  # noqa: E712
                FeedItem.source.has(Source.deleted_at.is_(None)),
            )
        )

        # Time filter
        if valid_time is not None:
            cutoff = datetime.utcnow() - timedelta(hours=valid_time)
            query = query.where(FeedItem.published_at >= cutoff)

        # Keyword filter (OR logic)
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(";") if k.strip()]
            if keyword_list:
                conditions = [
                    FeedItem.title.ilike(f"%{kw}%") for kw in keyword_list
                ]
                query = query.where(or_(*conditions))

        # Sorting
        if sort_by == "source":
            order_col = Source.name
            query = query.join(Source)
        else:
            order_col = FeedItem.published_at

        if sort_order == "desc":
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())

        result = await self.session.execute(query)
        return list(result.unique().scalars().all())

    def _generate_rss_xml(self, items: list[FeedItem]) -> str:
        """Generate RSS 2.0 XML from items.

        Args:
            items: List of FeedItem instances.

        Returns:
            RSS 2.0 XML string.
        """
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")

        # Channel metadata
        ET.SubElement(channel, "title").text = "RSS Aggregator"
        ET.SubElement(channel, "link").text = "https://github.com/rss-aggregator"
        ET.SubElement(channel, "description").text = "Aggregated RSS Feed"
        ET.SubElement(channel, "language").text = "en-us"
        ET.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        )

        # Items
        for item in items:
            item_elem = ET.SubElement(channel, "item")
            ET.SubElement(item_elem, "title").text = item.title
            ET.SubElement(item_elem, "link").text = item.link
            ET.SubElement(item_elem, "description").text = item.description or ""

            if item.published_at:
                ET.SubElement(item_elem, "pubDate").text = item.published_at.strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )

            if item.source:
                ET.SubElement(
                    item_elem, "source", url=item.source.url
                ).text = item.source.name

        return ET.tostring(rss, encoding="unicode", xml_declaration=True)