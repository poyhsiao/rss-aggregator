"""Fetch logs API routes."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session, require_api_key
from src.models import FetchLog
from src.utils.time import to_iso_string

router = APIRouter(prefix="/logs", tags=["logs"])


class LogResponse(BaseModel):
    """Schema for log response."""

    id: int
    source_id: int | None
    status: str
    log_type: str
    message: str
    items_count: int | None
    created_at: str


@router.get("", response_model=list[LogResponse])
async def get_logs(
    limit: int = Query(100, ge=1, le=1000),
    source_id: int | None = Query(None),
    status: str | None = Query(None, pattern="^(success|error)$"),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_api_key),
) -> list[LogResponse]:
    """Get fetch logs.

    Args:
        limit: Maximum number of logs to return.
        source_id: Filter by source ID (optional, returns all if not specified).
        status: Filter by status - 'success' or 'error' (optional, returns all if not specified).
    """
    query = select(FetchLog)

    if source_id is not None:
        query = query.where(FetchLog.source_id == source_id)

    if status is not None:
        query = query.where(FetchLog.status == status)

    query = query.order_by(FetchLog.created_at.desc()).limit(limit)

    result = await session.execute(query)
    logs = list(result.scalars().all())

    return [
        LogResponse(
            id=log.id,
            source_id=log.source_id,
            status=log.status,
            log_type=log.log_type,
            message=log.message,
            items_count=log.items_count,
            created_at=to_iso_string(log.created_at) or "",
        )
        for log in logs
    ]