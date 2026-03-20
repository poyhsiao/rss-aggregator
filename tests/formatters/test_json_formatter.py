"""Tests for JsonFormatter."""

import json
import pytest
from datetime import datetime

from src.formatters import JsonFormatter


def test_json_formatter_empty_items():
    """Test JSON formatter with empty items list."""
    formatter = JsonFormatter()
    result = formatter.format([])
    
    parsed = json.loads(result)
    assert parsed == []


def test_json_formatter_single_item():
    """Test JSON formatter with single item."""
    formatter = JsonFormatter()
    
    # Create a simple object as source
    class SimpleSource:
        def __init__(self):
            self.id = 1
            self.name = "Test Source"
    
    # Create a simple object as item
    class SimpleItem:
        def __init__(self):
            self.id = 1
            self.title = "Test Title"
            self.link = "https://example.com/article"
            self.description = "Test description"
            self.source = SimpleSource()
            self.published_at = datetime(2024, 1, 15, 10, 30, 0)
    
    item = SimpleItem()
    result = formatter.format([item])
    parsed = json.loads(result)
    
    assert len(parsed) == 1
    assert parsed[0]["id"] == 1
    assert parsed[0]["title"] == "Test Title"
    assert parsed[0]["link"] == "https://example.com/article"
    assert parsed[0]["description"] == "Test description"
    assert parsed[0]["source"] == "Test Source"
    assert "published_at" in parsed[0]


def test_json_formatter_content_type():
    """Test JSON formatter content type."""
    formatter = JsonFormatter()
    assert formatter.get_content_type() == "application/json"


def test_json_formatter_handles_none_description():
    """Test JSON formatter handles None description."""
    formatter = JsonFormatter()
    
    # Create a simple object as source
    class SimpleSource:
        def __init__(self):
            self.id = 1
            self.name = "Test Source"
    
    # Create a simple object as item
    class SimpleItem:
        def __init__(self):
            self.id = 1
            self.title = "Test Title"
            self.link = "https://example.com/article"
            self.description = None
            self.source = SimpleSource()
            self.published_at = datetime(2024, 1, 15, 10, 30, 0)
    
    item = SimpleItem()
    result = formatter.format([item])
    parsed = json.loads(result)
    
    assert parsed[0]["description"] == ""
