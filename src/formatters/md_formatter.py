"""Markdown formatter for feed items (extended format)."""

from typing import List

from src.config import settings
from src.formatters.base import BaseFormatter
from src.models import FeedItem


class MarkdownFormatter(BaseFormatter):
    """Formatter for Markdown output (extended format with metadata)."""

    def format(self, items: List[FeedItem]) -> str:
        """Format feed items as Markdown.

        Extended format includes: ID, Source URL, and other metadata.

        Args:
            items: List of FeedItem instances

        Returns:
            Markdown string
        """
        lines = ["# RSS Aggregator Feed\n"]

        if not items:
            lines.append("No items found.\n")
            return "".join(lines)

        lines.append("## Items\n")

        for item in items:
            lines.append(f"### {item.title}\n")
            lines.append(f"- **ID**: {item.id}\n")
            lines.append(f"- **Link**: {item.link}\n")

            if item.source:
                lines.append(f"- **Source**: {item.source.name}\n")
                lines.append(f"- **Source URL**: {item.source.url}\n")

            if item.published_at:
                formatted_date = item.published_at.strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"- **Published**: {formatted_date} ({settings.app_timezone})\n")

            if item.description:
                lines.append(f"\n{item.description}\n")

            lines.append("\n---\n")

        return "".join(lines)

    def get_content_type(self) -> str:
        """Return Markdown content type."""
        return "text/markdown"
