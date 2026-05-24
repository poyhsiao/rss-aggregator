"""Tests for FeedItem model database indexes."""

import pytest
from sqlalchemy import inspect

from src.models.feed_item import FeedItem


def test_feed_item_has_published_at_index():
    """FeedItem should have an index on published_at column."""
    mapper = inspect(FeedItem)
    table = mapper.tables[0]
    indexes = [idx for idx in table.indexes if idx.name == "ix_feed_item_published_at"]
    assert len(indexes) == 1, "Missing index on published_at"


def test_feed_item_has_source_id_index():
    """FeedItem should have an index on source_id column."""
    mapper = inspect(FeedItem)
    table = mapper.tables[0]
    indexes = [idx for idx in table.indexes if idx.name == "ix_feed_item_source_id"]
    assert len(indexes) == 1, "Missing index on source_id"


def test_feed_item_has_batch_id_index():
    """FeedItem should have an index on batch_id column."""
    mapper = inspect(FeedItem)
    table = mapper.tables[0]
    indexes = [idx for idx in table.indexes if idx.name == "ix_feed_item_batch_id"]
    assert len(indexes) == 1, "Missing index on batch_id"