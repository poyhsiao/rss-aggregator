"""Tests for backup service with feature flags."""

import pytest
from zipfile import ZipFile
import json
from io import BytesIO
from unittest.mock import MagicMock, AsyncMock, patch

from src.services.backup_service import BackupService
from src.services.feature_flag_service import FeatureFlagService


class TestBackupWithFeatureFlags:
    """Test backup export/import includes feature flags."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Create mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.get = AsyncMock()
        return db

    @pytest.fixture
    def backup_service(self, mock_db: MagicMock) -> BackupService:
        """Create BackupService instance."""
        return BackupService(mock_db)

    @pytest.fixture
    def ff_service(self, mock_db: MagicMock) -> FeatureFlagService:
        """Create FeatureFlagService instance."""
        return FeatureFlagService(mock_db)

    @pytest.fixture
    def seed_ff_data(self) -> dict:
        """Seed feature flag data."""
        return {
            "groups_enabled": False,
            "group_schedules_enabled": False,
            "source_group_schedules_enabled": True,
        }

    @pytest.mark.asyncio
    async def test_export_includes_feature_flags(
        self, backup_service: BackupService, seed_ff_data: dict
    ) -> None:
        """Export backup contains feature_flags field."""
        with patch.object(
            backup_service, "_serialize_data", new_callable=AsyncMock
        ) as mock_serialize, patch.object(
            FeatureFlagService, "get_all", new_callable=AsyncMock
        ) as mock_get_all:
            mock_serialize.return_value = {
                "sources": [],
                "feed_items": [],
                "api_keys": [],
                "preview_contents": [],
                "fetch_batches": [],
                "fetch_logs": [],
                "stats": [],
                "source_groups": [],
                "source_group_members": [],
            }
            mock_get_all.return_value = seed_ff_data

            result = await backup_service.export_backup()

            assert result is not None
            assert isinstance(result, bytes)

            # Decrypt and verify content
            from src.services.backup_password_provider import BackupPasswordProvider
            provider = BackupPasswordProvider()
            password = provider.get_password().encode()

            import pyzipper
            with pyzipper.AESZipFile(BytesIO(result), "r") as zf:
                zf.setpassword(password)
                content = zf.read("backup.json")
                data = json.loads(content)

            assert "feature_flags" in data["data"]
            assert data["data"]["feature_flags"]["groups_enabled"] == "false"
            assert data["data"]["feature_flags"]["group_schedules_enabled"] == "false"
            assert data["data"]["feature_flags"]["source_group_schedules_enabled"] == "true"

    @pytest.mark.asyncio
    async def test_import_restores_feature_flags(
        self, backup_service: BackupService, seed_ff_data: dict
    ) -> None:
        """Import backup restores feature_flags."""
        # Create backup with feature flags
        backup_data = {
            "version": "0.20.0",
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
                "source_groups": [],
                "source_group_members": [],
                "feature_flags": {
                    "groups_enabled": "false",
                    "group_schedules_enabled": "false",
                    "source_group_schedules_enabled": "true",
                },
            },
            "config": {"timezone": "Asia/Taipei", "language": "zh"},
        }
        json_data = json.dumps(backup_data).encode("utf-8")
        encrypted = backup_service._encrypt_zip(json_data)
        zip_bytes = encrypted.getvalue()

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

            with patch.object(
                FeatureFlagService, "upsert", new_callable=AsyncMock
            ) as mock_upsert:
                result = await backup_service.import_backup(zip_bytes)

                assert result.success is True
                # Verify upsert was called for each feature flag
                assert mock_upsert.call_count == 3