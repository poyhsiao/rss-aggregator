"""Tests for APIKey model."""

from src.models.api_key import APIKey


def test_api_key_model_has_required_fields():
    """Test that APIKey model has all required fields."""
    api_key = APIKey(
        key="test-api-key-12345",
        name="Test Key",
    )
    assert api_key.key == "test-api-key-12345"
    assert api_key.name == "Test Key"
    assert api_key.is_active is True


def test_api_key_name_is_optional():
    """Test that APIKey name is optional."""
    api_key = APIKey(key="test-key")
    assert api_key.name is None