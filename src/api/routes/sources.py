"""Source management API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict

from src.api.deps import get_feed_service, get_scheduler, get_source_group_service, get_source_service, require_api_key
from src.services.feed_service import FeedService
from src.services.source_group_service import SourceGroupService
from src.services.source_service import SourceService
from src.utils.time import to_iso_string

router = APIRouter(prefix="/sources", tags=["sources"])


class SourceCreate(BaseModel):
    """Schema for creating a source."""

    name: str
    url: str


class SourceUpdate(BaseModel):
    """Schema for updating a source."""

    name: str | None = None
    is_active: bool | None = None


class SourceResponse(BaseModel):
    """Schema for source response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    is_active: bool
    last_fetched_at: str | None
    last_error: str | None
    created_at: str
    updated_at: str
    groups: list[dict] = []


class BatchCreate(BaseModel):
    """Schema for batch source creation."""

    sources: list[SourceCreate]


@router.get("", response_model=list[SourceResponse])
async def list_sources(
    source_service: SourceService = Depends(get_source_service),
    group_service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> list[SourceResponse]:
    """List all sources."""
    sources = await source_service.get_sources()
    result = []
    for s in sources:
        groups = await group_service.get_source_groups(s.id)
        result.append(
            SourceResponse(
                id=s.id,
                name=s.name,
                url=s.url,
                is_active=s.is_active,
                last_fetched_at=to_iso_string(s.last_fetched_at),
                last_error=s.last_error,
                created_at=to_iso_string(s.created_at) or "",
                updated_at=to_iso_string(s.updated_at) or "",
                groups=[{"id": g.id, "name": g.name} for g in groups],
            )
        )
    return result


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    data: SourceCreate,
    source_service: SourceService = Depends(get_source_service),
    group_service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> SourceResponse:
    """Create a new source."""
    try:
        source = await source_service.create_source(
            name=data.name,
            url=data.url,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    groups = await group_service.get_source_groups(source.id)
    return SourceResponse(
        id=source.id,
        name=source.name,
        url=source.url,
        is_active=source.is_active,
        last_fetched_at=None,
        last_error=None,
        created_at=to_iso_string(source.created_at) or "",
        updated_at=to_iso_string(source.updated_at) or "",
        groups=[{"id": g.id, "name": g.name} for g in groups],
    )


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def batch_create_sources(
    data: BatchCreate,
    source_service: SourceService = Depends(get_source_service),
    group_service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> dict:
    """Batch create sources."""
    created = []
    errors = []

    for source_data in data.sources:
        try:
            source = await source_service.create_source(
                name=source_data.name,
                url=source_data.url,
            )
            groups = await group_service.get_source_groups(source.id)
            created.append({
                "id": source.id,
                "name": source.name,
                "groups": [{"id": g.id, "name": g.name} for g in groups],
            })
        except ValueError as e:
            errors.append({"url": source_data.url, "error": str(e)})

    return {"created": len(created), "sources": created, "errors": errors}


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: int,
    source_service: SourceService = Depends(get_source_service),
    group_service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> SourceResponse:
    """Get a specific source."""
    source = await source_service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    groups = await group_service.get_source_groups(source.id)
    return SourceResponse(
        id=source.id,
        name=source.name,
        url=source.url,
        is_active=source.is_active,
        last_fetched_at=to_iso_string(source.last_fetched_at),
        last_error=source.last_error,
        created_at=to_iso_string(source.created_at) or "",
        updated_at=to_iso_string(source.updated_at) or "",
        groups=[{"id": g.id, "name": g.name} for g in groups],
    )


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: int,
    data: SourceUpdate,
    source_service: SourceService = Depends(get_source_service),
    group_service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> SourceResponse:
    """Update a source."""
    try:
        source = await source_service.update_source(
            source_id,
            **{k: v for k, v in data.model_dump().items() if v is not None},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    groups = await group_service.get_source_groups(source.id)
    return SourceResponse(
        id=source.id,
        name=source.name,
        url=source.url,
        is_active=source.is_active,
        last_fetched_at=to_iso_string(source.last_fetched_at),
        last_error=source.last_error,
        created_at=to_iso_string(source.created_at) or "",
        updated_at=to_iso_string(source.updated_at) or "",
        groups=[{"id": g.id, "name": g.name} for g in groups],
    )


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: int,
    source_service: SourceService = Depends(get_source_service),
    _: str = Depends(require_api_key),
) -> None:
    """Delete a source (soft delete)."""
    try:
        await source_service.delete_source(source_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{source_id}/feed")
async def get_source_feed(
    source_id: int,
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
    feed_service: FeedService = Depends(get_feed_service),
    _: str = Depends(require_api_key),
) -> Response:
    """Get feed for a specific source.

    Returns RSS by default, or JSON/Markdown when format is specified.

    Query params:
    - format: Output format ('rss', 'json', or 'markdown', default: 'rss')
    - sort_by: Sort field ('published_at' or 'source')
    - sort_order: Sort direction ('asc' or 'desc')
    - valid_time: Time range in hours
    - keywords: Keywords for filtering (semicolon-separated)
    """
    source_service = SourceService(feed_service.session)
    source = await source_service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    content, content_type = await feed_service.get_formatted_feed(
        format=format,
        sort_by=sort_by,
        sort_order=sort_order,
        valid_time=valid_time,
        keywords=keywords,
        source_id=source_id,
    )
    return Response(content=content, media_type=content_type)


@router.post("/{source_id}/refresh")
async def refresh_source(
    source_id: int,
    scheduler=Depends(get_scheduler),
    _: str = Depends(require_api_key),
) -> dict:
    """Trigger refresh for a specific source."""
    await scheduler.refresh_source(source_id)
    return {"message": "Refresh triggered"}


@router.post("/refresh")
async def refresh_all_sources(
    scheduler=Depends(get_scheduler),
    _: str = Depends(require_api_key),
) -> dict:
    """Trigger refresh for all sources."""
    await scheduler.refresh_all()
    return {"message": "All sources refresh triggered"}