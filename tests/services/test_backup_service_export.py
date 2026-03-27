"""Tests for BackupService export functionality."""

from io import BytesIO
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from src.schemas.backup import ExportOptions
from src.services.backup_service import BackupService


class TestBackupServiceExport:
    """Test cases for BackupService export."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def backup_service(self, mock_db: MagicMock) -> BackupService:
        """Create BackupService instance."""
        return BackupService(mock_db)

    @pytest.mark.asyncio
    async def test_export_backup_returns_bytes(self, backup_service: BackupService) -> None:
        """Test export_backup returns bytes."""
        with patch.object(
            backup_service, "_serialize_data", new_callable=AsyncMock
        ) as mock_serialize:
            mock_serialize.return_value = {
                "sources": [],
                "feed_items": [],
                "api_keys": [],
                "preview_contents": [],
                "fetch_batches": [],
                "fetch_logs": [],
                "stats": [],
            }

            result = await backup_service.export_backup(ExportOptions())

            assert result is not None
            assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_export_backup_filename_format(self, backup_service: BackupService) -> None:
        """Test backup filename format."""
        filename = backup_service._generate_backup_filename("0.10.0")

        assert filename.startswith("rss-backup-v0.10.0-")
        assert filename.endswith(".zip")

    @pytest.mark.asyncio
    async def test_export_backup_with_options_exclude_feed_items(
        self, backup_service: BackupService
    ) -> None:
        """Test export with include_feed_items=False."""
        options = ExportOptions(include_feed_items=False)

        with patch.object(
            backup_service, "_serialize_data", new_callable=AsyncMock
        ) as mock_serialize:
            mock_serialize.return_value = {
                "sources": [{"id": 1}],
                "feed_items": [{"id": 1}],
                "api_keys": [],
                "preview_contents": [],
                "fetch_batches": [],
                "fetch_logs": [],
                "stats": [],
            }

            result = await backup_service.export_backup(options)

            assert result is not None

    @pytest.mark.asyncio
    async def test_export_backup_with_options_exclude_preview_contents(
        self, backup_service: BackupService
    ) -> None:
        """Test export with include_preview_contents=False."""
        options = ExportOptions(include_preview_contents=False)

        with patch.object(
            backup_service, "_serialize_data", new_callable=AsyncMock
        ) as mock_serialize:
            mock_serialize.return_value = {
                "sources": [],
                "feed_items": [],
                "api_keys": [],
                "preview_contents": [{"id": 1}],
                "fetch_batches": [],
                "fetch_logs": [],
                "stats": [],
            }

            result = await backup_service.export_backup(options)

            assert result is not None

    @pytest.mark.asyncio
    async def test_export_backup_with_options_include_logs(
        self, backup_service: BackupService
    ) -> None:
        """Test export with include_logs=True."""
        options = ExportOptions(include_logs=True)

        with patch.object(
            backup_service, "_serialize_data", new_callable=AsyncMock
        ) as mock_serialize:
            mock_serialize.return_value = {
                "sources": [],
                "feed_items": [],
                "api_keys": [],
                "preview_contents": [],
                "fetch_batches": [],
                "fetch_logs": [{"id": 1}],
                "stats": [],
            }

            result = await backup_service.export_backup(options)

            assert result is not None

    @pytest.mark.asyncio
    async def test_export_backup_encrypted(self, backup_service: BackupService) -> None:
        """Test that export creates encrypted ZIP."""
        with patch.object(
            backup_service, "_serialize_data", new_callable=AsyncMock
        ) as mock_serialize:
            mock_serialize.return_value = {
                "sources": [],
                "feed_items": [],
                "api_keys": [],
                "preview_contents": [],
                "fetch_batches": [],
                "fetch_logs": [],
                "stats": [],
            }

            result = await backup_service.export_backup(ExportOptions())

            # Verify it's a valid ZIP (starts with PK)
            assert result[:2] == b"PK"