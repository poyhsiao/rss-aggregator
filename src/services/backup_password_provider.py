"""Password provider for backup encryption."""

import os


class BackupPasswordProvider:
    """Provides password for backup encryption/decryption."""

    DEFAULT_PASSWORD = "kimhsiao"

    def get_password(self) -> str:
        """
        Get backup password from environment or return default.

        Returns:
            Password string from BACKUP_PASSWORD env var or default.
        """
        password = os.environ.get("BACKUP_PASSWORD", "").strip()
        return password if password else self.DEFAULT_PASSWORD
