"""Statistics API routes."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session, require_api_key
from src.models import Stats

router = APIRouter(prefix="/stats", tags=["stats"])


class StatsResponse(BaseModel):
    """Schema for stats response."""

    date: str
    total_requests: int
    successful_fetches: int
    failed_fetches: int


@router.get("", response_model=list[StatsResponse])
async def get_stats(
    days: int = Query(7, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_api_key),
) -> list[StatsResponse]:
    """Get statistics for the last N days."""
    start_date = date.today() - timedelta(days=days)

    result = await session.execute(
        select(Stats)
        .where(Stats.date >= start_date, Stats.deleted_at.is_(None))
        .order_by(Stats.date.desc())
    )
    stats = list(result.scalars().all())

    return [
        StatsResponse(
            date=str(s.date),
            total_requests=s.total_requests,
            successful_fetches=s.successful_fetches,
            failed_fetches=s.failed_fetches,
        )
        for s in stats
    ]