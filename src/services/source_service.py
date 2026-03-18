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
        self, name: str, url: str, fetch_interval: int = 900
    ) -> Source:
        """Create a new RSS source.

        Args:
            name: Display name for the source.
            url: URL of the RSS feed.
            fetch_interval: Interval in seconds between fetches. Defaults to 900.

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

        source = Source(name=name, url=url, fetch_interval=fetch_interval)
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