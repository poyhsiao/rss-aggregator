"""Feature flag service for managing feature flags."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from src.models.feature_flag import FeatureFlag

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


DEFAULT_FLAGS = {
    "groups_enabled": True,
    "group_schedules_enabled": True,
    "source_group_schedules_enabled": True,
}


class FeatureFlagService:
    """Service for managing feature flags."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize FeatureFlagService.

        Args:
            db: AsyncSession for database operations.
        """
        self._db = db

    async def get_all(self) -> dict[str, bool]:
        """Get all feature flags.

        Returns:
            Dictionary mapping flag keys to boolean values.
        """
        result = await self._db.execute(select(FeatureFlag))
        flags = {row.key: row.value for row in result.scalars().all()}

        # Merge with defaults for any missing flags
        merged = {}
        for key, default in DEFAULT_FLAGS.items():
            if key in flags:
                merged[key] = flags[key] == "true"
            else:
                merged[key] = default
        # Also include non-default flags
        for key, value in flags.items():
            if key not in merged:
                merged[key] = value == "true"
        return merged

    async def update(self, key: str, value: bool) -> None:
        """Update a single feature flag.

        Args:
            key: Flag key.
            value: New boolean value.
        """
        from src.utils.time import now

        flag = await self._db.get(FeatureFlag, key)
        if flag:
            flag.value = "true" if value else "false"
            flag.updated_at = now()
        else:
            self._db.add(FeatureFlag(key=key, value="true" if value else "false"))
        await self._db.commit()

    async def update_batch(self, flags: dict[str, bool]) -> None:
        """Batch update feature flags.

        Args:
            flags: Dictionary of flag keys to boolean values.
        """
        from src.utils.time import now

        for key, value in flags.items():
            flag = await self._db.get(FeatureFlag, key)
            if flag:
                flag.value = "true" if value else "false"
                flag.updated_at = now()
            else:
                self._db.add(FeatureFlag(key=key, value="true" if value else "false"))
        await self._db.commit()

    async def upsert(self, key: str, value: bool) -> None:
        """Insert or update a feature flag.

        Args:
            key: Flag key.
            value: Boolean value.
        """
        await self.update(key, value)