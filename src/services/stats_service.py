"""Service for managing daily statistics."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Stats


class StatsService:
    """Service for managing daily statistics."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service with a database session.

        Args:
            session: AsyncSession for database operations.
        """
        self.session = session

    async def increment_stats(
        self,
        stat_date: date | None = None,
        successful: bool = True,
    ) -> Stats:
        """Increment stats for a given date.

        Creates a new Stats entry if one doesn't exist for the date.

        Args:
            stat_date: Date to update. Defaults to today.
            successful: Whether the fetch was successful.

        Returns:
            The updated Stats instance.
        """
        if stat_date is None:
            stat_date = date.today()

        # Try to get existing stats for the date
        result = await self.session.execute(
            select(Stats).where(Stats.date == stat_date)
        )
        stats = result.scalar_one_or_none()

        if stats is None:
            # Create new stats entry
            stats = Stats(
                date=stat_date,
                total_requests=1,
                successful_fetches=1 if successful else 0,
                failed_fetches=0 if successful else 1,
            )
            self.session.add(stats)
        else:
            # Update existing stats
            stats.total_requests += 1
            if successful:
                stats.successful_fetches += 1
            else:
                stats.failed_fetches += 1

        await self.session.flush()
        return stats