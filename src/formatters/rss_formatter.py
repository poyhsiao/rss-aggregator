"""RSS 2.0 formatter for feed items."""

import xml.etree.ElementTree as ET
from typing import List

from src.formatters.base import BaseFormatter
from src.models import FeedItem
from src.utils.time import utcnow


class RssFormatter(BaseFormatter):
    """Formatter for RSS 2.0 XML output."""

    def format(self, items: List[FeedItem]) -> str:
        """Format feed items as RSS 2.0 XML.

        Args:
            items: List of FeedItem instances

        Returns:
            RSS 2.0 XML string
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

    def get_content_type(self) -> str:
        """Return RSS content type."""
        return "application/xml"
