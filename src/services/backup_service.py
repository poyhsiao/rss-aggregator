"""Backup and restore service."""

from __future__ import annotations

import io
from datetime import datetime, timezone, date
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from src.models import (
    APIKey,
    FeedItem,
    FetchBatch,
    FetchLog,
    PreviewContent,
    Source,
    Stats,
)
from src.schemas.backup import BackupConfig, BackupContent, BackupCounts
from src.services.backup_password_provider import BackupPasswordProvider

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


__version__ = "0.10.0"


class BackupService:
    """Service for backup and restore operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize BackupService.

        Args:
            db: AsyncSession for database operations.
        """
        self._db = db
        self._password_provider = BackupPasswordProvider()

    async def _get_all_sources(self) -> list[Source]:
        """Get all sources from database.

        Returns:
            List of all Source records.
        """
        result = await self._db.execute(select(Source))
        return list(result.scalars().all())

    async def _get_all_feed_items(self) -> list[FeedItem]:
        """Get all feed items from database.

        Returns:
            List of all FeedItem records.
        """
        result = await self._db.execute(select(FeedItem))
        return list(result.scalars().all())

    async def _get_all_api_keys(self) -> list[APIKey]:
        """Get all API keys from database.

        Returns:
            List of all APIKey records.
        """
        result = await self._db.execute(select(APIKey))
        return list(result.scalars().all())

    async def _get_all_preview_contents(self) -> list[PreviewContent]:
        """Get all preview contents from database.

        Returns:
            List of all PreviewContent records.
        """
        result = await self._db.execute(select(PreviewContent))
        return list(result.scalars().all())

    async def _get_all_fetch_batches(self) -> list[FetchBatch]:
        """Get all fetch batches from database.

        Returns:
            List of all FetchBatch records.
        """
        result = await self._db.execute(select(FetchBatch))
        return list(result.scalars().all())

    async def _get_all_fetch_logs(self) -> list[FetchLog]:
        """Get all fetch logs from database.

        Returns:
            List of all FetchLog records.
        """
        result = await self._db.execute(select(FetchLog))
        return list(result.scalars().all())

    async def _get_all_stats(self) -> list[Stats]:
        """Get all stats from database.

        Returns:
            List of all Stats records.
        """
        result = await self._db.execute(select(Stats))
        return list(result.scalars().all())

    def _serialize_model(self, obj: Any) -> dict[str, Any]:
        """Serialize a SQLAlchemy model to dictionary.

        Args:
            obj: SQLAlchemy model instance.

        Returns:
            Dictionary representation of the model.
        """
        result = {}
        for column in obj.__table__.columns:
            value = getattr(obj, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, date):
                value = value.isoformat()
            result[column.name] = value
        return result

    async def _serialize_data(self) -> dict[str, Any]:
        """Serialize all database data to dictionary.

        Returns:
            Dictionary containing all serialized data.
        """
        sources = await self._get_all_sources()
        feed_items = await self._get_all_feed_items()
        api_keys = await self._get_all_api_keys()
        preview_contents = await self._get_all_preview_contents()
        fetch_batches = await self._get_all_fetch_batches()
        fetch_logs = await self._get_all_fetch_logs()
        stats = await self._get_all_stats()

        return {
            "sources": [self._serialize_model(s) for s in sources],
            "feed_items": [self._serialize_model(f) for f in feed_items],
            "api_keys": [self._serialize_model(k) for k in api_keys],
            "preview_contents": [self._serialize_model(p) for p in preview_contents],
            "fetch_batches": [self._serialize_model(b) for b in fetch_batches],
            "fetch_logs": [self._serialize_model(l) for l in fetch_logs],
            "stats": [self._serialize_model(s) for s in stats],
        }

    def _get_config(self) -> dict[str, str]:
        """Get application config for backup.

        Returns:
            Dictionary with config values.
        """
        return {
            "timezone": "Asia/Taipei",
            "language": "zh",
        }

    def _generate_backup_filename(self, version: str) -> str:
        """Generate backup filename with version and date.

        Args:
            version: Application version.

        Returns:
            Filename string.
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"rss-backup-v{version}-{date_str}.zip"

    def _encrypt_zip(self, data: bytes) -> io.BytesIO:
        """Encrypt data as password-protected ZIP.

        Args:
            data: JSON data to encrypt.

        Returns:
            BytesIO with encrypted ZIP.
        """
        import pyzipper

        password = self._password_provider.get_password().encode()
        buffer = io.BytesIO()

        with pyzipper.AESZipFile(
            buffer, "w", compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES
        ) as zf:
            zf.setpassword(password)
            zf.writestr("backup.json", data)

        buffer.seek(0)
        return buffer

    def _decrypt_zip(self, zip_data: io.BytesIO) -> bytes:
        """Decrypt password-protected ZIP.

        Args:
            zip_data: Encrypted ZIP data.

        Returns:
            Decrypted JSON data bytes.

        Raises:
            ValueError: If decryption fails.
        """
        import pyzipper

        password = self._password_provider.get_password().encode()

        if hasattr(zip_data, "seek"):
            zip_data.seek(0)

        try:
            with pyzipper.AESZipFile(zip_data, "r") as zf:
                zf.setpassword(password)
                return zf.read("backup.json")
        except Exception as e:
            raise ValueError(f"Failed to decrypt backup: {e}") from e