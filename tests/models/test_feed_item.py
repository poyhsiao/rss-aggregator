"""Tests for FeedItem model."""

from datetime import datetime

from src.models.feed_item import FeedItem
from src.models.source import Source  # noqa: F401 - Required for SQLAlchemy registry


def test_feed_item_model_has_required_fields():
    """Test that FeedItem model has all required fields."""
    item = FeedItem(
        source_id=1,
        title="Test Article",
        link="https://example.com/article/1",
        description="This is a test article",
        published_at=datetime(2026, 3, 18, 10, 0, 0),
    )
    assert item.source_id == 1
    assert item.title == "Test Article"
    assert item.link == "https://example.com/article/1"
    assert item.description == "This is a test article"


def test_feed_item_optional_fields():
    """Test that FeedItem optional fields can be None."""
    item = FeedItem(
        source_id=1,
        title="Test",
        link="https://example.com/test",
    )
    assert item.description is None
    assert item.published_at is None