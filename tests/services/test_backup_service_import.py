"""Tests for BackupService import functionality."""

from io import BytesIO
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from src.schemas.backup import ImportResult
from src.services.backup_service import BackupService


class TestBackupServiceImport:
    """Test cases for BackupService import."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Create mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        return db

    @pytest.fixture
    def backup_service(self, mock_db: MagicMock) -> BackupService:
        """Create BackupService instance."""
        return BackupService(mock_db)

    @pytest.fixture
    def valid_backup_zip(self, backup_service: BackupService) -> bytes:
        """Create a valid backup ZIP for testing."""
        import json

        backup_data = {
            "version": "0.10.0",
            "exported_at": "2026-03-27T15:30:00+00:00",
            "app_name": "RSS-Aggregator",
            "data": {
                "sources": [],
                "feed_items": [],
                "api_keys": [],
                "preview_contents": [],
                "fetch_batches": [],
                "fetch_logs": [],
                "stats": [],
            },
            "config": {"timezone": "Asia/Taipei", "language": "zh"},
        }
        json_data = json.dumps(backup_data).encode("utf-8")
        encrypted = backup_service._encrypt_zip(json_data)
        return encrypted.getvalue()

    @pytest.mark.asyncio
    async def test_import_backup_returns_result(
        self, backup_service: BackupService, valid_backup_zip: bytes
    ) -> None:
        """Test import_backup returns ImportResult."""
        with patch.object(
            backup_service, "_get_all_sources", new_callable=AsyncMock
        ) as mock_sources, patch.object(
            backup_service, "_get_all_feed_items", new_callable=AsyncMock
        ) as mock_feed_items, patch.object(
            backup_service, "_get_all_api_keys", new_callable=AsyncMock
        ) as mock_api_keys, patch.object(
            backup_service, "_get_all_source_groups", new_callable=AsyncMock
        ) as mock_groups, patch.object(
            backup_service, "_get_all_source_group_members", new_callable=AsyncMock
        ) as mock_members:
            mock_sources.return_value = []
            mock_feed_items.return_value = []
            mock_api_keys.return_value = []
            mock_groups.return_value = []
            mock_members.return_value = []

            result = await backup_service.import_backup(valid_backup_zip)

            assert isinstance(result, ImportResult)
            assert result.success is True

    @pytest.mark.asyncio
    async def test_import_backup_invalid_zip(
        self, backup_service: BackupService
    ) -> None:
        """Test import with invalid ZIP data."""
        invalid_data = b"not a valid zip"

        result = await backup_service.import_backup(invalid_data)

        assert result.success is False
        assert "Failed to decrypt" in result.message or "Failed to parse" in result.message

    @pytest.mark.asyncio
    async def test_import_backup_version_incompatible(
        self, backup_service: BackupService
    ) -> None:
        """Test import with incompatible version."""
        import json

        backup_data = {
            "version": "1.0.0",  # Different major version
            "exported_at": "2026-03-27T15:30:00+00:00",
            "app_name": "RSS-Aggregator",
            "data": {
                "sources": [],
                "feed_items": [],
                "api_keys": [],
                "preview_contents": [],
                "fetch_batches": [],
                "fetch_logs": [],
                "stats": [],
            },
            "config": {"timezone": "Asia/Taipei", "language": "zh"},
        }
        json_data = json.dumps(backup_data).encode("utf-8")
        encrypted = backup_service._encrypt_zip(json_data)

        result = await backup_service.import_backup(encrypted.getvalue())

        assert result.success is False
        assert "Incompatible version" in result.message

    @pytest.mark.asyncio
    async def test_import_backup_with_sources(
        self, backup_service: BackupService
    ) -> None:
        """Test import with sources data."""
        import json

        backup_data = {
            "version": "0.10.0",
            "exported_at": "2026-03-27T15:30:00+00:00",
            "app_name": "RSS-Aggregator",
            "data": {
                "sources": [
                    {"id": 1, "url": "https://test.com/rss.xml", "name": "Test", "is_active": True}
                ],
                "feed_items": [],
                "api_keys": [],
                "preview_contents": [],
                "fetch_batches": [],
                "fetch_logs": [],
                "stats": [],
            },
            "config": {"timezone": "Asia/Taipei", "language": "zh"},
        }
        json_data = json.dumps(backup_data).encode("utf-8")
        encrypted = backup_service._encrypt_zip(json_data)

        with patch.object(
            backup_service, "_get_all_sources", new_callable=AsyncMock
        ) as mock_sources, patch.object(
            backup_service, "_get_all_feed_items", new_callable=AsyncMock
        ) as mock_feed_items, patch.object(
            backup_service, "_get_all_api_keys", new_callable=AsyncMock
        ) as mock_api_keys, patch.object(
            backup_service, "_get_all_source_groups", new_callable=AsyncMock
        ) as mock_groups, patch.object(
            backup_service, "_get_all_source_group_members", new_callable=AsyncMock
        ) as mock_members:
            mock_sources.return_value = []
            mock_feed_items.return_value = []
            mock_api_keys.return_value = []
            mock_groups.return_value = []
            mock_members.return_value = []

            result = await backup_service.import_backup(encrypted.getvalue())

            assert result.success is True
            assert result.summary is not None
            assert result.summary.sources_imported == 1

    @pytest.mark.asyncio
    async def test_import_backup_preview(
        self, backup_service: BackupService, valid_backup_zip: bytes
    ) -> None:
        """Test preview backup without importing."""
        preview = await backup_service.preview_backup(valid_backup_zip)

        assert preview is not None
        assert preview.version == "0.10.0"
        assert preview.counts is not None

    @pytest.mark.asyncio
    async def test_import_backup_with_source_groups(
        self, mock_db: MagicMock, backup_service: BackupService
    ) -> None:
        """Test import restores source groups and memberships."""
        import json

        backup_data = {
            "version": "0.10.0",
            "exported_at": "2026-03-27T15:30:00+00:00",
            "app_name": "RSS-Aggregator",
            "data": {
                "sources": [
                    {
                        "id": 1,
                        "url": "https://test.com/rss.xml",
                        "name": "Test Feed",
                        "is_active": True,
                    }
                ],
                "feed_items": [],
                "api_keys": [],
                "preview_contents": [],
                "fetch_batches": [],
                "fetch_logs": [],
                "stats": [],
                "source_groups": [
                    {
                        "id": 1,
                        "name": "Tech",
                        "created_at": "2026-03-27T10:00:00",
                        "updated_at": "2026-03-27T10:00:00",
                    }
                ],
                "source_group_members": [
                    {"source_id": 1, "group_id": 1},
                ],
            },
            "config": {"timezone": "Asia/Taipei", "language": "zh"},
        }
        json_data = json.dumps(backup_data).encode("utf-8")
        encrypted = backup_service._encrypt_zip(json_data)

        auto_id = 0
        added_objects: list = []
        original_add = mock_db.add

        def track_add(obj: object) -> None:
            added_objects.append(obj)
            original_add(obj)

        mock_db.add = MagicMock(side_effect=track_add)

        async def assign_ids() -> None:
            nonlocal auto_id
            for obj in added_objects:
                if hasattr(obj, "id") and obj.id is None:
                    auto_id += 1
                    obj.id = auto_id

        mock_db.flush = AsyncMock(side_effect=assign_ids)

        with patch.object(
            backup_service, "_get_all_sources", new_callable=AsyncMock
        ) as mock_sources, patch.object(
            backup_service, "_get_all_feed_items", new_callable=AsyncMock
        ) as mock_feed_items, patch.object(
            backup_service, "_get_all_api_keys", new_callable=AsyncMock
        ) as mock_api_keys, patch.object(
            backup_service, "_get_all_source_groups", new_callable=AsyncMock
        ) as mock_groups, patch.object(
            backup_service, "_get_all_source_group_members", new_callable=AsyncMock
        ) as mock_members:
            mock_sources.return_value = []
            mock_feed_items.return_value = []
            mock_api_keys.return_value = []
            mock_groups.return_value = []
            mock_members.return_value = []

            result = await backup_service.import_backup(encrypted.getvalue())

            assert result.success is True
            assert result.summary is not None
            assert result.summary.source_groups_imported == 1
            assert result.summary.source_group_members_imported == 1