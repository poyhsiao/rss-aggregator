"""Feed API routes."""

from typing import Any

from fastapi import APIRouter, Depends, Path, Query, Response

from src.api.deps import get_feed_service, require_api_key
from src.services.feed_service import FeedService

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("")
async def get_feed(
    format: str = Query(
        "rss",
        pattern="^(rss|json|markdown|preview)$",
        description="Output format: 'rss', 'json', 'markdown', or 'preview'",
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

    Returns RSS by default, or JSON/Markdown/Preview when format is specified.
    Supports filtering by time range, keywords, and source ID, and sorting.

    Query params:
    - format: Output format ('rss', 'json', 'markdown', or 'preview', default: 'rss')
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


@router.get("/{format}")
async def get_feed_by_format(
    format: str = Path(
        ...,
        pattern="^(rss|json|markdown|preview)$",
        description="Output format: 'rss', 'json', 'markdown', or 'preview'",
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
    """Get aggregated RSS feed by format path parameter.

    Returns RSS, JSON, or Markdown based on the format path parameter.
    Supports filtering by time range, keywords, source ID, and group ID.

    Path params:
    - format: Output format ('rss', 'json', or 'markdown')

    Query params:
    - sort_by: Sort field ('published_at' or 'source')
    - sort_order: Sort direction ('asc' or 'desc')
    - valid_time: Time range in hours
    - keywords: Keywords for filtering (semicolon-separated)
    - source_id: Filter by source ID
    - group_id: Filter by source group ID
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
