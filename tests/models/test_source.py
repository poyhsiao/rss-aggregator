"""Tests for Source model."""

from src.models.source import Source


def test_source_model_has_required_fields():
    """Test that Source model has all required fields."""
    source = Source(
        name="Test Source",
        url="https://example.com/feed.xml",
    )
    assert source.name == "Test Source"
    assert source.url == "https://example.com/feed.xml"
    assert source.is_active is True
    assert source.last_fetched_at is None
    assert source.last_error is None


def test_source_default_values():
    """Test that Source model has correct default values."""
    source = Source(
        name="Test",
        url="https://example.com/feed.xml",
    )
    assert source.is_active is True


def test_source_no_fetch_interval():
    """Source model should not have fetch_interval attribute."""
    source = Source(name="Test", url="https://example.com/rss")
    assert not hasattr(source, "fetch_interval")
