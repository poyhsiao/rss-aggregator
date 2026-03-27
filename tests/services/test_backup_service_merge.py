"""Tests for BackupService merge logic."""

from unittest.mock import MagicMock

import pytest

from src.services.backup_service import BackupService


class TestBackupServiceMerge:
    """Test cases for BackupService merge logic."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def backup_service(self, mock_db: MagicMock) -> BackupService:
        """Create BackupService instance."""
        return BackupService(mock_db)

    def test_is_version_compatible_same_major(self, backup_service: BackupService) -> None:
        """Test version compatibility with same major version."""
        assert backup_service._is_version_compatible("0.10.0", "0.11.0") is True
        assert backup_service._is_version_compatible("0.9.0", "0.10.0") is True

    def test_is_version_compatible_different_major(
        self, backup_service: BackupService
    ) -> None:
        """Test version compatibility with different major version."""
        assert backup_service._is_version_compatible("0.10.0", "1.0.0") is False
        assert backup_service._is_version_compatible("1.0.0", "2.0.0") is False

    def test_merge_sources_new_only(self, backup_service: BackupService) -> None:
        """Test merging sources that are all new."""
        existing: list[dict] = []
        backup = [
            {"id": 1, "url": "https://a.com/rss.xml", "name": "A"},
            {"id": 2, "url": "https://b.com/rss.xml", "name": "B"},
        ]

        merged, id_map = backup_service._merge_sources(existing, backup)

        assert len(merged) == 2
        assert id_map[1] == 1  # New source gets ID 1
        assert id_map[2] == 2  # New source gets ID 2

    def test_merge_sources_update_existing(self, backup_service: BackupService) -> None:
        """Test merging sources with updates to existing."""
        existing = [
            {"id": 1, "url": "https://a.com/rss.xml", "name": "A Old"},
        ]
        backup = [
            {"id": 1, "url": "https://a.com/rss.xml", "name": "A Updated"},
        ]

        merged, id_map = backup_service._merge_sources(existing, backup)

        assert len(merged) == 1
        assert merged[0]["name"] == "A Updated"
        assert id_map[1] == 1  # Existing ID preserved

    def test_merge_sources_mixed(self, backup_service: BackupService) -> None:
        """Test merging sources with mix of new and existing."""
        existing = [
            {"id": 1, "url": "https://a.com/rss.xml", "name": "A"},
        ]
        backup = [
            {"id": 1, "url": "https://a.com/rss.xml", "name": "A Updated"},
            {"id": 2, "url": "https://b.com/rss.xml", "name": "B"},
        ]

        merged, id_map = backup_service._merge_sources(existing, backup)

        assert len(merged) == 2
        assert id_map[1] == 1  # Existing ID preserved
        assert id_map[2] == 2  # New source gets new ID

    def test_merge_feed_items_new_only(self, backup_service: BackupService) -> None:
        """Test merging feed items that are all new."""
        existing: list[dict] = []
        backup = [
            {"id": 1, "link": "https://a.com/1", "title": "Article 1", "source_id": 1},
            {"id": 2, "link": "https://a.com/2", "title": "Article 2", "source_id": 1},
        ]
        source_id_map = {1: 10}  # Old source ID 1 maps to new ID 10

        merged = backup_service._merge_feed_items(existing, backup, source_id_map)

        assert len(merged) == 2
        assert merged[0]["source_id"] == 10  # ID remapped

    def test_merge_feed_items_update_existing(
        self, backup_service: BackupService
    ) -> None:
        """Test merging feed items with updates to existing."""
        existing = [
            {"id": 1, "link": "https://a.com/1", "title": "Old Title"},
        ]
        backup = [
            {"id": 1, "link": "https://a.com/1", "title": "Updated Title"},
        ]
        source_id_map = {}

        merged = backup_service._merge_feed_items(existing, backup, source_id_map)

        assert len(merged) == 1
        assert merged[0]["title"] == "Updated Title"

    def test_merge_api_keys_new_only(self, backup_service: BackupService) -> None:
        """Test merging API keys that are all new."""
        existing: list[dict] = []
        backup = [
            {"id": 1, "key": "key1", "name": "Key 1"},
            {"id": 2, "key": "key2", "name": "Key 2"},
        ]

        merged = backup_service._merge_api_keys(existing, backup)

        assert len(merged) == 2

    def test_merge_api_keys_update_existing(
        self, backup_service: BackupService
    ) -> None:
        """Test merging API keys with updates to existing."""
        existing = [
            {"id": 1, "key": "key1", "name": "Old Name"},
        ]
        backup = [
            {"id": 1, "key": "key1", "name": "New Name"},
        ]

        merged = backup_service._merge_api_keys(existing, backup)

        assert len(merged) == 1
        assert merged[0]["name"] == "New Name"

    def test_merge_api_keys_different_key(
        self, backup_service: BackupService
    ) -> None:
        """Test merging API keys with different keys adds new."""
        existing = [
            {"id": 1, "key": "key1", "name": "Key 1"},
        ]
        backup = [
            {"id": 2, "key": "key2", "name": "Key 2"},
        ]

        merged = backup_service._merge_api_keys(existing, backup)

        assert len(merged) == 2