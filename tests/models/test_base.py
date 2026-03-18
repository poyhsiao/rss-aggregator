"""Tests for base model functionality."""

from src.models.base import Base, TimestampMixin


def test_timestamp_mixin_has_required_fields():
    """Test that TimestampMixin has all required timestamp fields."""
    mixin = TimestampMixin()
    assert hasattr(mixin, "created_at")
    assert hasattr(mixin, "updated_at")
    assert hasattr(mixin, "deleted_at")


def test_base_is_declarative_base():
    """Test that Base is a valid declarative base."""
    assert hasattr(Base, "metadata")
    assert hasattr(Base, "registry")