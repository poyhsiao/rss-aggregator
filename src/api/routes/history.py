"""History API routes."""

from datetime import date

from fastapi import APIRouter, Depends, Query

from src.api.deps import get_history_service, require_api_key
from src.schemas.history import HistoryResponse
from src.services.history_service import HistoryService

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=HistoryResponse)
async def get_history(
    start_date: date | None = Query(
        None,
        description="Start date (ISO 8601 format, e.g., 2024-01-01)",
    ),
    end_date: date | None = Query(
        None,
        description="End date (ISO 8601 format, e.g., 2024-01-31)",
    ),
    source_ids: str | None = Query(
        None,
        description="Source IDs (comma-separated, e.g., 1,2,3)",
    ),
    keywords: str | None = Query(
        None,
        description="Keywords for title filtering (semicolon-separated)",
    ),
    sort_by: str = Query(
        "fetched_at",
        pattern="^(fetched_at|published_at)$",
        description="Sort field",
    ),
    sort_order: str = Query(
        "desc",
        pattern="^(asc|desc)$",
        description="Sort direction",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    history_service: HistoryService = Depends(get_history_service),
    _: str = Depends(require_api_key),
) -> HistoryResponse:
    """Get historical feed items with filtering and pagination."""
    # Parse source_ids from comma-separated string
    source_id_list = None
    if source_ids:
        source_id_list = [int(sid.strip()) for sid in source_ids.split(",") if sid.strip()]

    items, pagination = await history_service.get_history(
        start_date=start_date,
        end_date=end_date,
        source_ids=source_id_list,
        keywords=keywords,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    return HistoryResponse(items=items, pagination=pagination)
