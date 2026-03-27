"""Trash management API routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.deps import get_source_service, require_api_key
from src.services.source_service import SourceService
from src.utils.time import to_iso_string

router = APIRouter(prefix="/trash", tags=["trash"])


class TrashItemResponse(BaseModel):
    """Schema for trash item response."""

    id: int
    name: str
    url: str
    fetch_interval: int
    is_active: bool
    deleted_at: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class RestoreRequest(BaseModel):
    """Schema for restore request."""

    conflict_resolution: str | None = None


class RestoreResponse(BaseModel):
    """Schema for restore response."""

    id: int
    name: str
    restored: bool


@router.get("", response_model=list[TrashItemResponse])
async def list_trash(
    source_service: SourceService = Depends(get_source_service),
    _: str = Depends(require_api_key),
) -> list[TrashItemResponse]:
    """List all trash items."""
    sources = await source_service.get_trash_sources()
    return [
        TrashItemResponse(
            id=s.id,
            name=s.name,
            url=s.url,
            fetch_interval=s.fetch_interval,
            is_active=s.is_active,
            deleted_at=to_iso_string(s.deleted_at) or "",
            created_at=to_iso_string(s.created_at) or "",
            updated_at=to_iso_string(s.updated_at) or "",
        )
        for s in sources
    ]


@router.post("/{source_id}/restore")
async def restore_source(
    source_id: int,
    request: RestoreRequest | None = None,
    source_service: SourceService = Depends(get_source_service),
    _: str = Depends(require_api_key),
):
    """Restore a trash item.

    Returns 409 if conflict detected and no resolution provided.
    """
    request = request or RestoreRequest()

    try:
        conflict = await source_service.check_restore_conflict(source_id)

        if conflict:
            if request.conflict_resolution == "overwrite":
                source = await source_service.restore_source(source_id, overwrite=True)
                return RestoreResponse(id=source.id, name=source.name, restored=True)
            elif request.conflict_resolution == "keep_existing":
                trash = await source_service.get_trash_source(source_id)
                if trash is None:
                    raise HTTPException(status_code=404, detail="Trash item not found")
                return RestoreResponse(id=trash.id, name=trash.name, restored=False)
            else:
                trash = await source_service.get_trash_source(source_id)
                if trash is None:
                    raise HTTPException(status_code=404, detail="Trash item not found")
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "conflict_detected",
                        "message": "A source with this name or URL already exists",
                        "conflict": {
                            "trash_item": {
                                "id": trash.id,
                                "name": trash.name,
                                "url": trash.url,
                            },
                            "existing_item": {
                                "id": conflict["existing_item"].id,
                                "name": conflict["existing_item"].name,
                                "url": conflict["existing_item"].url,
                            },
                            "conflict_type": conflict["conflict_type"],
                        },
                    }
                )

        source = await source_service.restore_source(source_id)
        return RestoreResponse(id=source.id, name=source.name, restored=True)

    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail="Trash item not found")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{source_id}")
async def permanent_delete_source(
    source_id: int,
    source_service: SourceService = Depends(get_source_service),
    _: str = Depends(require_api_key),
):
    """Permanently delete a trash item."""
    try:
        await source_service.permanent_delete_source(source_id)
        return {"deleted": True}
    except ValueError:
        raise HTTPException(status_code=404, detail="Trash item not found")


@router.delete("")
async def clear_trash(
    source_service: SourceService = Depends(get_source_service),
    _: str = Depends(require_api_key),
):
    """Clear all trash items."""
    count = await source_service.clear_trash()
    return {"deleted_count": count}