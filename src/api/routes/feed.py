"""Feed API routes."""

from typing import Any

from fastapi import APIRouter, Depends, Query, Response

from src.api.deps import get_feed_service, require_api_key
from src.services.feed_service import FeedService

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("")
async def get_feed(
    format: str = Query(
        "rss",
        pattern="^(rss|json|markdown)$",
        description="Output format: 'rss', 'json', or 'markdown'",
    ),
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
    source_id: int | None = Query(
        None,
        description="Filter by source ID",
    ),
    group_id: int | None = Query(
        None,
        description="Filter by source group ID",
    ),
    feed_service: FeedService = Depends(get_feed_service),
    _: str = Depends(require_api_key),
) -> Any:
    """Get aggregated RSS feed.

    Returns RSS by default, or JSON/Markdown when format is specified.
    Supports filtering by time range, keywords, and source ID, and sorting.

    Query params:
    - format: Output format ('rss', 'json', or 'markdown', default: 'rss')
    - sort_by: Sort field ('published_at' or 'source')
    - sort_order: Sort direction ('asc' or 'desc')
    - valid_time: Time range in hours
    - keywords: Keywords for filtering (semicolon-separated)
    - source_id: Filter by source ID
    """
    content, content_type = await feed_service.get_formatted_feed(
        format=format,
        sort_by=sort_by,
        sort_order=sort_order,
        valid_time=valid_time,
        keywords=keywords,
        source_id=source_id,
        group_id=group_id,
    )
    return Response(content=content, media_type=content_type)
