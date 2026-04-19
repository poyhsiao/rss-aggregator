from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Response

from src.api.deps import get_feed_service, get_history_service, require_api_key
from src.schemas.history import (
    DeleteBatchResponse,
    DeleteHistoryResponse,
    HistoryBatch,
    HistoryBatchesResponse,
    HistoryResponse,
    UpdateBatchNameRequest,
)
from src.services.feed_service import FeedService
from src.services.history_service import HistoryService

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/batches", response_model=HistoryBatchesResponse)
async def get_history_batches(
    limit: int = Query(50, ge=1, le=100, description="Number of batches to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    group_id: int | None = Query(None, description="Filter by source group ID"),
    history_service: HistoryService = Depends(get_history_service),
    _: str = Depends(require_api_key),
) -> HistoryBatchesResponse:
    return await history_service.get_history_batches(limit=limit, offset=offset, group_id=group_id)


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


@router.patch("/batches/{batch_id}/name", response_model=HistoryBatch)
async def update_batch_name(
    batch_id: int = Path(..., description="The batch ID to update"),
    request: UpdateBatchNameRequest = Body(...),
    history_service: HistoryService = Depends(get_history_service),
    _: str = Depends(require_api_key),
) -> HistoryBatch:
    result = await history_service.update_batch_name(batch_id, request)
    if not result:
        raise HTTPException(status_code=404, detail="Batch not found")
    return result


@router.delete("/batches/{batch_id}", response_model=DeleteBatchResponse)
async def delete_batch(
    batch_id: int = Path(..., description="The batch ID to delete"),
    history_service: HistoryService = Depends(get_history_service),
    _: str = Depends(require_api_key),
) -> DeleteBatchResponse:
    success = await history_service.delete_batch(batch_id)
    if not success:
        raise HTTPException(status_code=404, detail="Batch not found")
    return DeleteBatchResponse(success=True)


@router.delete("/", response_model=DeleteHistoryResponse)
async def delete_all_history(
    history_service: HistoryService = Depends(get_history_service),
    _: str = Depends(require_api_key),
) -> DeleteHistoryResponse:
    deleted_count = await history_service.delete_all_history()
    return DeleteHistoryResponse(success=True, deleted_count=deleted_count)


@router.delete("/by-group/{group_id}", response_model=DeleteHistoryResponse)
async def delete_history_by_group(
    group_id: int = Path(..., description="The group ID to delete history for"),
    history_service: HistoryService = Depends(get_history_service),
    _: str = Depends(require_api_key),
) -> DeleteHistoryResponse:
    deleted_count = await history_service.delete_history_by_group(group_id)
    if deleted_count < 0:
        raise HTTPException(status_code=404, detail="Group not found")
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="No history found for this group")
    return DeleteHistoryResponse(success=True, deleted_count=deleted_count)


@router.get("/batches/{batch_id}/{format}")
async def get_history_batch_feed(
    batch_id: int = Path(..., description="The batch ID"),
    format: str = Path(..., pattern="^(rss|json|markdown|preview)$", description="Output format"),
    sort_by: str = Query(
        "published_at",
        pattern="^(published_at|source)$",
        description="Sort by field",
    ),
    sort_order: str = Query(
        "desc",
        pattern="^(asc|desc)$",
        description="Sort direction",
    ),
    history_service: HistoryService = Depends(get_history_service),
    feed_service: FeedService = Depends(get_feed_service),
    _: str = Depends(require_api_key),
) -> Response:
    """Get feed for a specific history batch in RSS/JSON/Markdown/Preview format.

    Path params:
    - batch_id: Batch ID
    - format: Output format ('rss', 'json', 'markdown', or 'preview')
    """
    # Check if batch exists
    batch = await history_service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Get feed items for this batch
    feed_items = await history_service.get_batch_raw_items(batch_id)

    # Format as feed
    content, content_type = await feed_service.format_items_as_feed(
        items=feed_items,
        format=format,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return Response(content=content, media_type=content_type)