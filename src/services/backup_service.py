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

    def _is_version_compatible(
        self, backup_version: str, current_version: str
    ) -> bool:
        """Check version compatibility.

        Rules:
        - Same major version: Compatible
        - Different major version: Incompatible

        Args:
            backup_version: Version from backup file.
            current_version: Current application version.

        Returns:
            True if versions are compatible.
        """
        backup_major = backup_version.split(".")[0]
        current_major = current_version.split(".")[0]
        return backup_major == current_major

    def _merge_sources(
        self,
        existing: list[dict[str, Any]],
        backup: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], dict[int, int]]:
        """Merge sources, keyed by URL.

        Args:
            existing: Existing sources from database.
            backup: Sources from backup.

        Returns:
            Tuple of (merged sources, old_id to new_id mapping).
        """
        existing_by_url = {s["url"]: s for s in existing}
        merged = list(existing)
        id_map: dict[int, int] = {}

        for source in backup:
            if source["url"] in existing_by_url:
                # Update existing
                existing_source = existing_by_url[source["url"]]
                id_map[source["id"]] = existing_source["id"]
                # Update fields
                for key, value in source.items():
                    if key != "id":
                        existing_source[key] = value
            else:
                # Add new source
                new_id = len(merged) + 1
                new_source = {**source, "id": new_id}
                id_map[source["id"]] = new_id
                merged.append(new_source)

        return merged, id_map

    def _merge_feed_items(
        self,
        existing: list[dict[str, Any]],
        backup: list[dict[str, Any]],
        source_id_map: dict[int, int],
    ) -> list[dict[str, Any]]:
        """Merge feed items, keyed by link.

        Args:
            existing: Existing feed items from database.
            backup: Feed items from backup.
            source_id_map: Mapping of old source IDs to new IDs.

        Returns:
            Merged feed items.
        """
        existing_by_link = {f["link"]: f for f in existing}
        merged = list(existing)

        for item in backup:
            # Remap source_id if present
            if "source_id" in item and item["source_id"] in source_id_map:
                item = {**item, "source_id": source_id_map[item["source_id"]]}

            if item["link"] in existing_by_link:
                # Update existing
                existing_item = existing_by_link[item["link"]]
                for key, value in item.items():
                    if key != "id":
                        existing_item[key] = value
            else:
                # Add new item
                new_id = len(merged) + 1
                merged.append({**item, "id": new_id})

        return merged

    def _merge_api_keys(
        self,
        existing: list[dict[str, Any]],
        backup: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Merge API keys, keyed by key string.

        Args:
            existing: Existing API keys from database.
            backup: API keys from backup.

        Returns:
            Merged API keys.
        """
        existing_by_key = {k["key"]: k for k in existing}
        merged = list(existing)

        for key in backup:
            if key["key"] in existing_by_key:
                # Update existing
                existing_key = existing_by_key[key["key"]]
                for k, v in key.items():
                    if k != "id":
                        existing_key[k] = v
            else:
                # Add new key
                new_id = len(merged) + 1
                merged.append({**key, "id": new_id})

        return merged