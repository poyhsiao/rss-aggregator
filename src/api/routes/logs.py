"""Error logs API routes."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session, require_api_key
from src.models import ErrorLog

router = APIRouter(prefix="/logs", tags=["logs"])


class LogResponse(BaseModel):
    """Schema for log response."""

    id: int
    source_id: int | None
    error_type: str
    error_message: str
    created_at: str


@router.get("", response_model=list[LogResponse])
async def get_logs(
    limit: int = Query(100, ge=1, le=1000),
    source_id: int | None = Query(None),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_api_key),
) -> list[LogResponse]:
    """Get recent error logs."""
    query = select(ErrorLog).where(ErrorLog.deleted_at.is_(None))

    if source_id:
        query = query.where(ErrorLog.source_id == source_id)

    query = query.order_by(ErrorLog.created_at.desc()).limit(limit)

    result = await session.execute(query)
    logs = list(result.scalars().all())

    return [
        LogResponse(
            id=log.id,
            source_id=log.source_id,
            error_type=log.error_type,
            error_message=log.error_message,
            created_at=log.created_at.isoformat(),
        )
        for log in logs
    ]