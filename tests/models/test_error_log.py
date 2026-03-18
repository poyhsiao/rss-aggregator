"""Tests for ErrorLog model."""

from src.models.error_log import ErrorLog
from src.models.feed_item import FeedItem  # noqa: F401 - Required for SQLAlchemy registry
from src.models.source import Source  # noqa: F401 - Required for SQLAlchemy registry


def test_error_log_model_has_required_fields():
    """Test that ErrorLog model has all required fields."""
    log = ErrorLog(
        error_type="HTTPError",
        error_message="Connection timeout",
    )
    assert log.error_type == "HTTPError"
    assert log.error_message == "Connection timeout"
    assert log.source_id is None


def test_error_log_with_source():
    """Test that ErrorLog can be associated with a source."""
    log = ErrorLog(
        source_id=1,
        error_type="ParseError",
        error_message="Invalid RSS format",
    )
    assert log.source_id == 1