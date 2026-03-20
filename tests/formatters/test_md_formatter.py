"""Tests for MarkdownFormatter."""

import pytest
from datetime import datetime

from src.formatters import MarkdownFormatter
from src.models import FeedItem, Source


@pytest.fixture
def test_source():
    """Create a test Source instance without persisting to DB."""
    source = Source(name="Test Source", url="https://example.com/feed")
    source.id = 1  # Set id manually for testing
    return source


@pytest.fixture
def test_item(test_source):
    """Create a test FeedItem instance."""
    item = FeedItem(
        title="Test Title",
        link="https://example.com/article",
        description="Test description",
        source_id=1,
        published_at=datetime(2024, 1, 15, 10, 30, 0),
    )
    item.id = 1  # Set id manually for testing
    item.source = test_source
    return item


def test_md_formatter_empty_items():
    """Test Markdown formatter with empty items list."""
    formatter = MarkdownFormatter()
    result = formatter.format([])
    
    assert "# RSS Aggregator Feed" in result
    assert "No items found." in result


def test_md_formatter_single_item(test_item):
    """Test Markdown formatter with single item (extended format)."""
    formatter = MarkdownFormatter()
    result = formatter.format([test_item])
    
    # Extended format includes:
    assert "# RSS Aggregator Feed" in result
    assert "## Items" in result
    assert "### Test Title" in result
    assert "**ID**: 1" in result
    assert "**Link**: https://example.com/article" in result
    assert "**Source**: Test Source" in result
    assert "**Source URL**: https://example.com/feed" in result
    assert "**Published**:" in result
    assert "Test description" in result


def test_md_formatter_content_type():
    """Test Markdown formatter content type."""
    formatter = MarkdownFormatter()
    assert formatter.get_content_type() == "text/markdown"


def test_md_formatter_multiple_items(test_source):
    """Test Markdown formatter with multiple items."""
    formatter = MarkdownFormatter()
    
    item1 = FeedItem(
        title="First Article",
        link="https://example.com/1",
        description="First description",
        source_id=1,
        published_at=datetime(2024, 1, 15, 10, 30, 0),
    )
    item1.id = 1
    item1.source = test_source
    
    item2 = FeedItem(
        title="Second Article",
        link="https://example.com/2",
        description="Second description",
        source_id=1,
        published_at=datetime(2024, 1, 16, 11, 0, 0),
    )
    item2.id = 2
    item2.source = test_source
    
    result = formatter.format([item1, item2])
    
    assert "### First Article" in result
    assert "### Second Article" in result
    assert "---" in result  # Separator between items
