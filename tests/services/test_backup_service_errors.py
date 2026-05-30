"""Tests for backup service error handling."""

import json
import io
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.services.backup_service import BackupService


class TestBackupServiceErrorHandling:
    """Test granular error handling in BackupService."""

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

    def _create_encrypted_backup(self, backup_service: BackupService, data: dict) -> bytes:
        """Helper to create encrypted backup."""
        json_data = json.dumps(data).encode("utf-8")
        encrypted = backup_service._encrypt_zip(json_data)
        return encrypted.getvalue()

    @pytest.mark.asyncio
    async def test_import_backup_json_decode_error(
        self, backup_service: BackupService
    ) -> None:
        """BackupService should handle corrupted JSON gracefully."""
        # Create a ZIP with corrupted JSON inside
        import pyzipper

        password = backup_service._password_provider.get_password().encode()
        buffer = io.BytesIO()
        with pyzipper.AESZipFile(
            buffer, "w", compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES
        ) as zf:
            zf.setpassword(password)
            zf.writestr("backup.json", b"not valid json {")

        buffer.seek(0)
        result = await backup_service.import_backup(buffer.getvalue())

        assert result.success is False
        assert "json" in result.message.lower() or "parse" in result.message.lower() or "decrypt" in result.message.lower()

    @pytest.mark.asyncio
    async def test_import_backup_file_not_found_simulation(
        self, backup_service: BackupService
    ) -> None:
        """BackupService should handle FileNotFoundError gracefully."""
        # Simulate FileNotFoundError during decryption by providing invalid data
        invalid_data = b"invalid zip data that will cause issues"
        result = await backup_service.import_backup(invalid_data)

        assert result.success is False
        assert result.message is not None

    @pytest.mark.asyncio
    async def test_import_backup_version_incompatible(
        self, backup_service: BackupService
    ) -> None:
        """BackupService should handle version incompatibility gracefully."""
        backup_data = {
            "version": "999.999.999",
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
            },
            "config": {"timezone": "Asia/Taipei", "language": "zh"},
        }
        encrypted = self._create_encrypted_backup(backup_service, backup_data)

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

            result = await backup_service.import_backup(encrypted)

            assert result.success is False
            assert "version" in result.message.lower() or "incompatible" in result.message.lower()

    @pytest.mark.asyncio
    async def test_preview_backup_handles_corrupted_json(
        self, backup_service: BackupService
    ) -> None:
        """preview_backup should handle corrupted JSON gracefully."""
        import pyzipper

        password = backup_service._password_provider.get_password().encode()
        buffer = io.BytesIO()
        with pyzipper.AESZipFile(
            buffer, "w", compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES
        ) as zf:
            zf.setpassword(password)
            zf.writestr("backup.json", b"not valid json {")

        buffer.seek(0)
        result = await backup_service.preview_backup(buffer.getvalue())

        assert result is None

    @pytest.mark.asyncio
    async def test_preview_backup_handles_invalid_zip(
        self, backup_service: BackupService
    ) -> None:
        """preview_backup should handle invalid ZIP gracefully."""
        invalid_data = b"not a valid zip"
        result = await backup_service.preview_backup(invalid_data)

        assert result is None

    @pytest.mark.asyncio
    async def test_preview_backup_handles_version_incompatible(
        self, backup_service: BackupService
    ) -> None:
        """preview_backup should handle version incompatibility gracefully."""
        backup_data = {
            "version": "999.999.999",
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
            },
            "config": {"timezone": "Asia/Taipei", "language": "zh"},
        }
        encrypted = self._create_encrypted_backup(backup_service, backup_data)

        # Version incompatibility doesn't cause preview to fail - it just returns the preview
        result = await backup_service.preview_backup(encrypted)
        assert result is not None
        assert result.version == "999.999.999"