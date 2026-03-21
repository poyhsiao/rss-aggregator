"""Tests for Source model."""

from src.models.source import Source


def test_source_model_has_required_fields():
    """Test that Source model has all required fields."""
    source = Source(
        name="Test Source",
        url="https://example.com/feed.xml",
        fetch_interval=900,
    )
    assert source.name == "Test Source"
    assert source.url == "https://example.com/feed.xml"
    assert source.fetch_interval == 900
    assert source.is_active is True
    assert source.last_fetched_at is None
    assert source.last_error is None


def test_source_default_values():
    """Test that Source model has correct default values."""
    source = Source(
        name="Test",
        url="https://example.com/feed.xml",
    )
    assert source.fetch_interval == 0
    assert source.is_active is True
