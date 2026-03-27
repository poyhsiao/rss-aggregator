"""Tests for BackupPasswordProvider."""

import os
from unittest.mock import patch

import pytest

from src.services.backup_password_provider import BackupPasswordProvider


class TestBackupPasswordProvider:
    """Test cases for BackupPasswordProvider."""

    def test_get_password_from_env(self) -> None:
        """Test password from environment variable."""
        with patch.dict(os.environ, {"BACKUP_PASSWORD": "test_password"}):
            provider = BackupPasswordProvider()
            assert provider.get_password() == "test_password"

    def test_get_password_default(self) -> None:
        """Test default password when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove BACKUP_PASSWORD if exists
            os.environ.pop("BACKUP_PASSWORD", None)
            provider = BackupPasswordProvider()
            assert provider.get_password() == "kimhsiao"

    def test_get_password_empty_string_uses_default(self) -> None:
        """Test empty string in env var uses default."""
        with patch.dict(os.environ, {"BACKUP_PASSWORD": ""}):
            provider = BackupPasswordProvider()
            assert provider.get_password() == "kimhsiao"

    def test_get_password_whitespace_uses_default(self) -> None:
        """Test whitespace-only env var uses default."""
        with patch.dict(os.environ, {"BACKUP_PASSWORD": "   "}):
            provider = BackupPasswordProvider()
            assert provider.get_password() == "kimhsiao"

    def test_default_password_constant(self) -> None:
        """Test default password constant value."""
        assert BackupPasswordProvider.DEFAULT_PASSWORD == "kimhsiao"
