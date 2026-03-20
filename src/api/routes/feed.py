"""Feed API routes."""

from typing import Any

from fastapi import APIRouter, Depends, Query

from src.api.deps import get_feed_service, require_api_key
from src.services.feed_service import FeedService

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("")
async def get_feed(
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
    valid_time: int | None = Query(
        None,
        ge=1,
        description="Time range in hours",
    ),
    keywords: str | None = Query(
        None,
        description="Keywords (semicolon-separated)",
    ),
    feed_service: FeedService = Depends(get_feed_service),
    _: str = Depends(require_api_key),
) -> list[dict[str, Any]]:
    """Get aggregated RSS feed items.

    Returns JSON array with items from all active sources.
    Supports filtering by time range and keywords, and sorting.
    """
    return await feed_service.get_feed_items(
        sort_by=sort_by,
        sort_order=sort_order,
        valid_time=valid_time,
        keywords=keywords,
    )