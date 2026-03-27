"""Schemas for backup and restore functionality."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BackupConfig(BaseModel):
    """Application configuration in backup."""

    timezone: str = "Asia/Taipei"
    language: str = "zh"


class BackupCounts(BaseModel):
    """Counts of items in backup."""

    sources: int = 0
    feed_items: int = 0
    api_keys: int = 0
    preview_contents: int = 0
    fetch_batches: int = 0
    fetch_logs: int = 0
    stats: int = 0


class BackupContent(BaseModel):
    """Full backup content structure."""

    version: str
    exported_at: str
    app_name: str = "RSS-Aggregator"
    data: dict[str, Any]
    config: BackupConfig = Field(default_factory=BackupConfig)


class ExportOptions(BaseModel):
    """Options for export backup."""

    include_feed_items: bool = True
    include_preview_contents: bool = True
    include_logs: bool = False


class ImportSummary(BaseModel):
    """Summary of import operation."""

    sources_imported: int = 0
    sources_merged: int = 0
    feed_items_imported: int = 0
    api_keys_imported: int = 0


class ImportResult(BaseModel):
    """Result of import operation."""

    success: bool
    message: str
    summary: ImportSummary | None = None


class BackupPreview(BaseModel):
    """Preview of backup content."""

    version: str
    exported_at: str
    counts: BackupCounts
    config: BackupConfig
