"""Tests for PreviewContent model."""

from src.models.preview_content import PreviewContent


def test_preview_content_model_has_required_fields():
    """Test that PreviewContent model has all required fields."""
    preview = PreviewContent(
        url="https://example.com/article",
        url_hash="a" * 64,  # SHA-256 hex string is 64 chars
        markdown_content="# Test Article\n\nContent here.",
        title="Test Article",
    )
    assert preview.url == "https://example.com/article"
    assert preview.url_hash == "a" * 64
    assert preview.markdown_content == "# Test Article\n\nContent here."
    assert preview.title == "Test Article"


def test_preview_content_url_max_length():
    """Test that PreviewContent accepts URLs up to 2048 characters."""
    base = "https://example.com/"
    padding = 2048 - len(base)
    long_url = base + "a" * padding
    preview = PreviewContent(
        url=long_url,
        url_hash="x" * 64,
        markdown_content="content",
    )
    assert len(preview.url) == 2048


def test_preview_content_title_optional():
    """Test that PreviewContent allows None for title."""
    preview = PreviewContent(
        url="https://example.com/article",
        url_hash="x" * 64,
        markdown_content="content",
        title=None,
    )
    assert preview.title is None


def test_preview_content_default_title_is_none():
    """Test that title defaults to None."""
    preview = PreviewContent(
        url="https://example.com/article",
        url_hash="x" * 64,
        markdown_content="content",
    )
    assert preview.title is None