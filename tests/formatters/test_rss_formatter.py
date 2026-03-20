"""Tests for RssFormatter."""

import pytest
from datetime import datetime

from src.formatters import RssFormatter
from src.models import FeedItem, Source


def test_rss_formatter_empty_items():
    """Test RSS formatter with empty items list."""
    formatter = RssFormatter()
    result = formatter.format([])

    assert "<?xml version" in result
    assert "<rss version=\"2.0\"" in result
    assert "<channel>" in result
    assert "</channel>" in result
    assert "</rss>" in result


def test_rss_formatter_single_item():
    """Test RSS formatter with single item."""
    formatter = RssFormatter()

    source = Source(name="Test Source", url="https://example.com/feed")
    item = FeedItem(
        title="Test Title",
        link="https://example.com/article",
        description="Test description",
        source_id=1,
        published_at=datetime(2024, 1, 15, 10, 30, 0),
    )
    object.__setattr__(item, "source", source)

    result = formatter.format([item])

    assert "<title>Test Title</title>" in result
    assert "<link>https://example.com/article</link>" in result
    assert "<description>Test description</description>" in result
    assert "<source url=\"https://example.com/feed\">Test Source</source>" in result


def test_rss_formatter_content_type():
    """Test RSS formatter content type."""
    formatter = RssFormatter()
    assert formatter.get_content_type() == "application/xml"
