"""Tests for Stats model."""

from datetime import date

from src.models.stats import Stats


def test_stats_model_has_required_fields():
    """Test that Stats model has all required fields."""
    stats = Stats(
        date=date(2026, 3, 18),
        total_requests=100,
        successful_fetches=50,
        failed_fetches=2,
    )
    assert stats.date == date(2026, 3, 18)
    assert stats.total_requests == 100
    assert stats.successful_fetches == 50
    assert stats.failed_fetches == 2


def test_stats_default_values():
    """Test that Stats model has correct default values."""
    stats = Stats(date=date(2026, 3, 18))
    assert stats.total_requests == 0
    assert stats.successful_fetches == 0
    assert stats.failed_fetches == 0