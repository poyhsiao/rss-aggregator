"""RSS 2.0 formatter for feed items."""

import xml.etree.ElementTree as ET
from typing import List

from src.formatters.base import BaseFormatter
from src.models import FeedItem
from src.utils.time import utcnow


def prettify_xml(xml_str: str) -> str:
    """Format XML string with proper indentation."""
    try:
        root = ET.fromstring(xml_str)
        ET.indent(root, space="  ")
        result = ET.tostring(root, encoding="unicode")
        # Restore XML declaration if original had it
        if xml_str.startswith('<?xml'):
            result = '<?xml version="1.0" encoding="utf-8"?>\n' + result
        return result
    except ET.ParseError:
        # If parsing fails, return original
        return xml_str


class RssFormatter(BaseFormatter):
    """Formatter for RSS 2.0 XML output."""

    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def _cdata(self, text: str) -> str:
        """Wrap text in CDATA section."""
        return f"<![CDATA[{text}]]>"

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
            ET.SubElement(item_elem, "description").text = self._cdata(
                item.description or ""
            )

            if item.published_at:
                ET.SubElement(item_elem, "pubDate").text = item.published_at.strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )

            if item.source:
                ET.SubElement(
                    item_elem, "source", url=item.source.url
                ).text = item.source.name

        # Use a custom approach: serialize with CDATA preserved
        xml_str = ET.tostring(rss, encoding="unicode", xml_declaration=True)
        # Replace XML-escaped CDATA with actual CDATA
        return xml_str.replace(
            "&lt;![CDATA[", "<![CDATA["
        ).replace(
            "]]&gt;", "]]>"
        )

    def get_content_type(self) -> str:
        """Return RSS content type."""
        return "application/xml"
