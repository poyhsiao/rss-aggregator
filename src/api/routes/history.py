from fastapi import APIRouter, Depends, Path, Query

from src.api.deps import get_history_service, require_api_key
from src.schemas.history import HistoryBatchesResponse, HistoryResponse
from src.services.history_service import HistoryService

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/batches", response_model=HistoryBatchesResponse)
async def get_history_batches(
    limit: int = Query(50, ge=1, le=100, description="Number of batches to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    history_service: HistoryService = Depends(get_history_service),
    _: str = Depends(require_api_key),
) -> HistoryBatchesResponse:
    return await history_service.get_history_batches(limit=limit, offset=offset)


@router.get("/batches/{batch_id}", response_model=HistoryResponse)
async def get_history_by_batch(
    batch_id: int = Path(..., description="The batch ID to fetch items for"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    history_service: HistoryService = Depends(get_history_service),
    _: str = Depends(require_api_key),
) -> HistoryResponse:
    items, pagination = await history_service.get_history_by_batch(
        batch_id=batch_id,
        page=page,
        page_size=page_size,
    )
    return HistoryResponse(items=items, pagination=pagination)