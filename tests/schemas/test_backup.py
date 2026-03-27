"""Tests for backup schemas."""

from datetime import datetime

import pytest

from src.schemas.backup import (
    BackupConfig,
    BackupContent,
    BackupCounts,
    BackupPreview,
    ExportOptions,
    ImportResult,
    ImportSummary,
)


class TestBackupSchemas:
    """Test cases for backup schemas."""

    def test_backup_config_defaults(self) -> None:
        """Test BackupConfig with default values."""
        config = BackupConfig()
        assert config.timezone == "Asia/Taipei"
        assert config.language == "zh"

    def test_backup_config_custom(self) -> None:
        """Test BackupConfig with custom values."""
        config = BackupConfig(timezone="UTC", language="en")
        assert config.timezone == "UTC"
        assert config.language == "en"

    def test_backup_counts_defaults(self) -> None:
        """Test BackupCounts with default values."""
        counts = BackupCounts()
        assert counts.sources == 0
        assert counts.feed_items == 0
        assert counts.api_keys == 0

    def test_backup_counts_custom(self) -> None:
        """Test BackupCounts with custom values."""
        counts = BackupCounts(sources=5, feed_items=100, api_keys=1)
        assert counts.sources == 5
        assert counts.feed_items == 100
        assert counts.api_keys == 1

    def test_export_options_defaults(self) -> None:
        """Test ExportOptions with default values."""
        options = ExportOptions()
        assert options.include_feed_items is True
        assert options.include_preview_contents is True
        assert options.include_logs is False

    def test_import_summary_defaults(self) -> None:
        """Test ImportSummary with default values."""
        summary = ImportSummary()
        assert summary.sources_imported == 0
        assert summary.sources_merged == 0

    def test_import_result_success(self) -> None:
        """Test ImportResult success case."""
        result = ImportResult(success=True, message="OK")
        assert result.success is True
        assert result.message == "OK"
        assert result.summary is None

    def test_backup_preview(self) -> None:
        """Test BackupPreview."""
        preview = BackupPreview(
            version="0.10.0",
            exported_at="2026-03-27T15:30:00+08:00",
            counts=BackupCounts(sources=5),
            config=BackupConfig(),
        )
        assert preview.version == "0.10.0"
        assert preview.counts.sources == 5

    def test_backup_content(self) -> None:
        """Test BackupContent."""
        content = BackupContent(
            version="0.10.0",
            exported_at="2026-03-27T15:30:00+08:00",
            data={"sources": []},
        )
        assert content.version == "0.10.0"
        assert content.app_name == "RSS-Aggregator"
        assert content.data == {"sources": []}
