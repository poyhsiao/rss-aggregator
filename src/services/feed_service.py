"""Service for aggregating and filtering RSS feeds."""

import xml.etree.ElementTree as ET
from datetime import timedelta
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.formatters import get_formatter
from src.models import FeedItem, Source
from src.utils.time import now, to_iso_string, utcnow


class FeedService:
    """Service for aggregating RSS feeds."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service with a database session.

        Args:
            session: AsyncSession for database operations.
        """
        self.session = session

    async def get_formatted_feed(
        self,
        format: str = "rss",
        sort_by: str = "published_at",
        sort_order: str = "desc",
        valid_time: int | None = None,
        keywords: str | None = None,
        source_id: int | None = None,
        group_id: int | None = None,
    ) -> tuple[str, str]:
        """Get formatted feed in specified format.

        Args:
            format: Output format ("rss", "json", or "markdown").
            sort_by: Sort field ("published_at" or "source").
            sort_order: Sort direction ("asc" or "desc").
            valid_time: Time range in hours (None = all items).
            keywords: Semicolon-separated keywords for title filtering.
            source_id: Filter by source ID (None = all sources).
            group_id: Filter by source group ID (None = all groups).

        Returns:
            tuple[str, str]: (formatted content, MIME type)
        """
        items = await self._fetch_items(
            sort_by=sort_by,
            sort_order=sort_order,
            valid_time=valid_time,
            keywords=keywords,
            source_id=source_id,
            group_id=group_id,
        )
        formatter = get_formatter(format)
        return formatter.format(items), formatter.get_content_type()

    async def get_aggregated_feed(
        self,
        sort_by: str = "published_at",
        sort_order: str = "desc",
        valid_time: int | None = None,
        keywords: str | None = None,
    ) -> str:
        """Get aggregated RSS feed (legacy method for backward compatibility).

        Returns:
            RSS 2.0 XML string.
        """
        content, _ = await self.get_formatted_feed(
            format="rss",
            sort_by=sort_by,
            sort_order=sort_order,
            valid_time=valid_time,
            keywords=keywords,
        )
        return content

    async def _fetch_items(
        self,
        sort_by: str,
        sort_order: str,
        valid_time: int | None,
        keywords: str | None,
        source_id: int | None = None,
        group_id: int | None = None,
    ) -> list[FeedItem]:
        """Fetch filtered feed items from database."""
        query = (
            select(FeedItem)
            .options(
                joinedload(FeedItem.source).joinedload(Source.groups)
            )
            .where(
                FeedItem.source.has(Source.is_active == True),  # noqa: E712
                FeedItem.source.has(Source.deleted_at.is_(None)),
            )
        )

        if group_id is not None:
            query = query.where(
                FeedItem.source.has(
                    Source.groups.any(id=group_id)
                )
            )

        if valid_time is not None:
            cutoff = now() - timedelta(hours=valid_time)
            query = query.where(FeedItem.published_at >= cutoff)

        if keywords:
            keyword_list = [k.strip() for k in keywords.split(";") if k.strip()]
            if keyword_list:
                conditions = [
                    FeedItem.title.ilike(f"%{kw}%") for kw in keyword_list
                ]
                query = query.where(or_(*conditions))

        if source_id is not None:
            query = query.where(FeedItem.source_id == source_id)

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
        items = list(result.unique().scalars().all())

        seen_links: set[str] = set()
        deduplicated_items: list[FeedItem] = []
        for item in items:
            if item.link not in seen_links:
                seen_links.add(item.link)
                deduplicated_items.append(item)

        return deduplicated_items

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
        ET.SubElement(channel, "lastBuildDate").text = utcnow().strftime(
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

    async def get_feed_items(
        self,
        sort_by: str = "published_at",
        sort_order: str = "desc",
        valid_time: int | None = None,
        keywords: str | None = None,
        source_id: int | None = None,
        group_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get feed items as list of dictionaries.

        Args:
            sort_by: Sort field ("published_at" or "source").
            sort_order: Sort direction ("asc" or "desc").
            valid_time: Time range in hours (None = all items).
            keywords: Semicolon-separated keywords for title filtering.
            source_id: Filter by source ID (None = all sources).
            group_id: Filter by source group ID (None = all groups).

        Returns:
            List of feed item dictionaries.
        """
        items = await self._fetch_items(
            sort_by=sort_by,
            sort_order=sort_order,
            valid_time=valid_time,
            keywords=keywords,
            source_id=source_id,
            group_id=group_id,
        )
        return [
            {
                "id": item.id,
                "title": item.title,
                "link": item.link,
                "description": item.description or "",
                "source": item.source.name if item.source else "",
                "published_at": to_iso_string(item.published_at),
                "source_groups": [
                    {"id": g.id, "name": g.name}
                    for g in item.source.groups
                ] if item.source else [],
            }
            for item in items
        ]