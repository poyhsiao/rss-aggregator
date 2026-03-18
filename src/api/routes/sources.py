"""Source management API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.deps import get_scheduler, get_source_service, require_api_key
from src.services.source_service import SourceService

router = APIRouter(prefix="/sources", tags=["sources"])


class SourceCreate(BaseModel):
    """Schema for creating a source."""

    name: str
    url: str
    fetch_interval: int = 900


class SourceUpdate(BaseModel):
    """Schema for updating a source."""

    name: str | None = None
    fetch_interval: int | None = None
    is_active: bool | None = None


class SourceResponse(BaseModel):
    """Schema for source response."""

    id: int
    name: str
    url: str
    fetch_interval: int
    is_active: bool
    last_fetched_at: str | None
    last_error: str | None

    class Config:
        from_attributes = True


class BatchCreate(BaseModel):
    """Schema for batch source creation."""

    sources: list[SourceCreate]


@router.get("", response_model=list[SourceResponse])
async def list_sources(
    source_service: SourceService = Depends(get_source_service),
    _: str = Depends(require_api_key),
) -> list[SourceResponse]:
    """List all sources."""
    sources = await source_service.get_sources()
    return [
        SourceResponse(
            id=s.id,
            name=s.name,
            url=s.url,
            fetch_interval=s.fetch_interval,
            is_active=s.is_active,
            last_fetched_at=s.last_fetched_at.isoformat() if s.last_fetched_at else None,
            last_error=s.last_error,
        )
        for s in sources
    ]


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    data: SourceCreate,
    source_service: SourceService = Depends(get_source_service),
    _: str = Depends(require_api_key),
) -> SourceResponse:
    """Create a new source."""
    try:
        source = await source_service.create_source(
            name=data.name,
            url=data.url,
            fetch_interval=data.fetch_interval,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return SourceResponse(
        id=source.id,
        name=source.name,
        url=source.url,
        fetch_interval=source.fetch_interval,
        is_active=source.is_active,
        last_fetched_at=None,
        last_error=None,
    )


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def batch_create_sources(
    data: BatchCreate,
    source_service: SourceService = Depends(get_source_service),
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
                fetch_interval=source_data.fetch_interval,
            )
            created.append({"id": source.id, "name": source.name})
        except ValueError as e:
            errors.append({"url": source_data.url, "error": str(e)})

    return {"created": len(created), "sources": created, "errors": errors}


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: int,
    source_service: SourceService = Depends(get_source_service),
    _: str = Depends(require_api_key),
) -> SourceResponse:
    """Get a specific source."""
    source = await source_service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    return SourceResponse(
        id=source.id,
        name=source.name,
        url=source.url,
        fetch_interval=source.fetch_interval,
        is_active=source.is_active,
        last_fetched_at=source.last_fetched_at.isoformat() if source.last_fetched_at else None,
        last_error=source.last_error,
    )


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: int,
    data: SourceUpdate,
    source_service: SourceService = Depends(get_source_service),
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

    return SourceResponse(
        id=source.id,
        name=source.name,
        url=source.url,
        fetch_interval=source.fetch_interval,
        is_active=source.is_active,
        last_fetched_at=source.last_fetched_at.isoformat() if source.last_fetched_at else None,
        last_error=source.last_error,
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


@router.post("/{source_id}/refresh")
async def refresh_source(
    source_id: int,
    scheduler=Depends(get_scheduler),
    _: str = Depends(require_api_key),
) -> dict:
    """Trigger refresh for a specific source."""
    if scheduler is None:
        raise HTTPException(status_code=503, detail="Scheduler not available")

    await scheduler.refresh_source(source_id)
    return {"message": "Refresh triggered"}


@router.post("/refresh")
async def refresh_all_sources(
    scheduler=Depends(get_scheduler),
    _: str = Depends(require_api_key),
) -> dict:
    """Trigger refresh for all sources."""
    if scheduler is None:
        raise HTTPException(status_code=503, detail="Scheduler not available")

    await scheduler.refresh_all()
    return {"message": "All sources refresh triggered"}