"""JSON formatter for feed items."""

import json
from typing import List

from src.formatters.base import BaseFormatter
from src.models import FeedItem
from src.utils.time import to_iso_string


class JsonFormatter(BaseFormatter):
    """Formatter for JSON output."""

    def format(self, items: List[FeedItem]) -> str:
        """Format feed items as JSON array.

        Args:
            items: List of FeedItem instances

        Returns:
            JSON string
        """
        data = []
        for item in items:
            # Safe access to source - avoid triggering lazy loads
            source_name = ""
            source_id = None
            if item.source:
                source_name = item.source.name
                source_id = item.source_id

            data.append({
                "id": item.id,
                "title": item.title,
                "link": item.link,
                "description": item.description or "",
                "source": source_name,
                "source_id": source_id,
                "published_at": to_iso_string(item.published_at),
            })
        return json.dumps(data, indent=2)

    def get_content_type(self) -> str:
        """Return JSON content type."""
        return "application/json"
