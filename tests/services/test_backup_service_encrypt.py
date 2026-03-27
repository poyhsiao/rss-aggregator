"""Tests for BackupService encryption methods."""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from src.services.backup_service import BackupService


class TestBackupServiceEncrypt:
    """Test cases for BackupService encryption."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def backup_service(self, mock_db: MagicMock) -> BackupService:
        """Create BackupService instance."""
        return BackupService(mock_db)

    def test_encrypt_and_decrypt_roundtrip(self, backup_service: BackupService) -> None:
        """Test encrypt and decrypt roundtrip."""
        data = b"test data content"

        encrypted = backup_service._encrypt_zip(data)
        assert encrypted is not None
        assert isinstance(encrypted, BytesIO)

        decrypted = backup_service._decrypt_zip(encrypted)
        assert decrypted == data

    def test_encrypt_creates_valid_zip(self, backup_service: BackupService) -> None:
        """Test encrypted data is a valid ZIP."""
        import zipfile

        data = b"content for zip"
        encrypted = backup_service._encrypt_zip(data)

        # Should be able to open as ZIP
        with zipfile.ZipFile(encrypted, "r") as zf:
            assert zf.namelist() == ["backup.json"]

    def test_encrypt_with_different_password_fails(
        self, backup_service: BackupService
    ) -> None:
        """Test decryption with wrong password fails."""
        from src.services.backup_password_provider import BackupPasswordProvider

        data = b"secret data"
        encrypted = backup_service._encrypt_zip(data)

        # Create service with different password
        different_provider = BackupPasswordProvider()
        different_provider.DEFAULT_PASSWORD = "wrong_password"

        with patch.object(
            backup_service, "_password_provider", different_provider
        ):
            with pytest.raises(Exception):  # pyzipper raises exception for wrong password
                backup_service._decrypt_zip(encrypted)

    def test_encrypt_empty_data(self, backup_service: BackupService) -> None:
        """Test encrypting empty data."""
        data = b""
        encrypted = backup_service._encrypt_zip(data)
        assert encrypted is not None

        decrypted = backup_service._decrypt_zip(encrypted)
        assert decrypted == data

    def test_encrypt_large_data(self, backup_service: BackupService) -> None:
        """Test encrypting large data."""
        data = b"x" * 1_000_000  # 1MB
        encrypted = backup_service._encrypt_zip(data)
        assert encrypted is not None

        decrypted = backup_service._decrypt_zip(encrypted)
        assert decrypted == data

    def test_decrypt_invalid_data_raises(
        self, backup_service: BackupService
    ) -> None:
        """Test decrypting invalid data raises error."""
        invalid_data = BytesIO(b"not a valid zip file")

        with pytest.raises(ValueError, match="Failed to decrypt backup"):
            backup_service._decrypt_zip(invalid_data)