"""Output formatters for feed items."""

from src.formatters.base import BaseFormatter
from src.formatters.rss_formatter import RssFormatter
from src.formatters.json_formatter import JsonFormatter
from src.formatters.md_formatter import MarkdownFormatter

__all__ = [
    "BaseFormatter",
    "RssFormatter",
    "JsonFormatter",
    "MarkdownFormatter",
    "get_formatter",
]

# Valid format types
FormatType = str  # "rss", "json", or "markdown"


def get_formatter(format: str) -> BaseFormatter:
    """Factory function to get appropriate formatter.

    Falls back to RSS formatter for invalid format values (lenient mode).

    Args:
        format: Output format string ("rss", "json", or "markdown")

    Returns:
        Appropriate formatter instance
    """
    formatters = {
        "rss": RssFormatter(),
        "json": JsonFormatter(),
        "markdown": MarkdownFormatter(),
    }
    # Lenient mode: fallback to RSS for invalid formats
    return formatters.get(format.lower(), formatters["rss"])
