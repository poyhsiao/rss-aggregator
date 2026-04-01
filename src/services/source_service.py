"""Service for managing RSS sources."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Source


class SourceService:
    """Service for managing RSS feed sources."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service with a database session.

        Args:
            session: AsyncSession for database operations.
        """
        self.session = session

    async def create_source(
        self, name: str, url: str
    ) -> Source:
        """Create a new RSS source.

        Args:
            name: Display name for the source.
            url: URL of the RSS feed.

        Returns:
            The created Source instance.

        Raises:
            ValueError: If a source with the same URL already exists.
        """
        # Check for existing URL
        existing = await self.session.execute(
            select(Source).where(Source.url == url, Source.deleted_at.is_(None))
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Source with URL '{url}' already exists")

        source = Source(name=name, url=url)
        self.session.add(source)
        await self.session.commit()
        await self.session.refresh(source)
        return source

    async def get_sources(self, include_deleted: bool = False) -> list[Source]:
        """Get all sources.

        Args:
            include_deleted: Whether to include soft-deleted sources.

        Returns:
            List of Source instances.
        """
        query = select(Source)
        if not include_deleted:
            query = query.where(Source.deleted_at.is_(None))

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_source(self, source_id: int) -> Source | None:
        """Get a source by ID.

        Args:
            source_id: ID of the source to retrieve.

        Returns:
            Source instance if found and not deleted, None otherwise.
        """
        result = await self.session.execute(
            select(Source).where(Source.id == source_id, Source.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def update_source(self, source_id: int, **kwargs) -> Source:
        """Update a source.

        Args:
            source_id: ID of the source to update.
            **kwargs: Fields to update.

        Returns:
            Updated Source instance.

        Raises:
            ValueError: If source not found.
        """
        source = await self.get_source(source_id)
        if source is None:
            raise ValueError(f"Source with id {source_id} not found")

        for key, value in kwargs.items():
            if hasattr(source, key):
                setattr(source, key, value)

        await self.session.commit()
        await self.session.refresh(source)
        return source

    async def delete_source(self, source_id: int) -> None:
        """Soft delete a source.

        Args:
            source_id: ID of the source to delete.

        Raises:
            ValueError: If source not found.
        """
        source = await self.get_source(source_id)
        if source is None:
            raise ValueError(f"Source with id {source_id} not found")

        source.soft_delete()
        await self.session.commit()

    async def get_active_sources(self) -> list[Source]:
        """Get all active sources for fetching.

        Returns:
            List of active Source instances.
        """
        result = await self.session.execute(
            select(Source).where(
                Source.is_active.is_(True), Source.deleted_at.is_(None)
            )
        )
        return list(result.scalars().all())

    # ==================== Trash Management ====================

    async def get_trash_sources(self) -> list[Source]:
        """Get all soft-deleted sources.

        Returns:
            List of soft-deleted Source instances.
        """
        result = await self.session.execute(
            select(Source).where(Source.deleted_at.is_not(None))
        )
        return list(result.scalars().all())

    async def get_trash_source(self, source_id: int) -> Source | None:
        """Get a single trash source by ID.

        Args:
            source_id: ID of the source to retrieve.

        Returns:
            Source if found and soft-deleted, None otherwise.
        """
        result = await self.session.execute(
            select(Source).where(
                Source.id == source_id,
                Source.deleted_at.is_not(None)
            )
        )
        return result.scalar_one_or_none()

    async def check_restore_conflict(self, source_id: int) -> dict | None:
        """Check if restoring would cause a conflict.

        Args:
            source_id: ID of the trash source to check.

        Returns:
            None if no conflict, or dict with 'existing_item' and 'conflict_type'.

        Raises:
            ValueError: If trash item not found.
        """
        trash_source = await self.get_trash_source(source_id)
        if trash_source is None:
            raise ValueError(f"Trash source with id {source_id} not found")

        name_result = await self.session.execute(
            select(Source).where(
                Source.name == trash_source.name,
                Source.deleted_at.is_(None)
            )
        )
        name_existing = name_result.scalar_one_or_none()

        url_result = await self.session.execute(
            select(Source).where(
                Source.url == trash_source.url,
                Source.deleted_at.is_(None)
            )
        )
        url_existing = url_result.scalar_one_or_none()

        existing = name_existing or url_existing
        if existing is None:
            return None

        if name_existing and url_existing:
            conflict_type = "both"
        elif name_existing:
            conflict_type = "name"
        else:
            conflict_type = "url"

        return {
            "existing_item": existing,
            "conflict_type": conflict_type
        }

    async def restore_source(self, source_id: int, overwrite: bool = False) -> Source:
        trash_source = await self.get_trash_source(source_id)
        if trash_source is None:
            raise ValueError(f"Trash source with id {source_id} not found")

        if overwrite:
            conflict = await self.check_restore_conflict(source_id)
            if conflict:
                conflict["existing_item"].soft_delete()
                await self.session.commit()
        else:
            conflict = await self.check_restore_conflict(source_id)
            if conflict:
                raise ValueError(
                    f"Conflict detected: {conflict['conflict_type']} already exists"
                )

        trash_source.deleted_at = None
        await self.session.commit()
        await self.session.refresh(trash_source)
        return trash_source

    async def permanent_delete_source(self, source_id: int) -> None:
        """Permanently delete a soft-deleted source.

        Args:
            source_id: ID of the source to permanently delete.

        Raises:
            ValueError: If source not found or not in trash.
        """
        source = await self.get_trash_source(source_id)
        if source is None:
            raise ValueError(f"Trash source with id {source_id} not found")

        await self.session.delete(source)
        await self.session.commit()

    async def clear_trash(self) -> int:
        """Permanently delete all soft-deleted sources.

        Returns:
            Number of sources permanently deleted.
        """
        result = await self.session.execute(
            select(Source).where(Source.deleted_at.is_not(None))
        )
        sources = list(result.scalars().all())
        count = len(sources)

        for source in sources:
            await self.session.delete(source)

        await self.session.commit()
        return count