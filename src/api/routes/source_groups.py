"""Source group management API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from src.api.deps import get_source_group_service, require_api_key
from src.services.source_group_service import SourceGroupService
from src.utils.time import to_iso_string

router = APIRouter(prefix="/source-groups", tags=["source-groups"])


class GroupCreate(BaseModel):
    name: str


class GroupUpdate(BaseModel):
    name: str | None = None


class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    member_count: int = 0
    created_at: str
    updated_at: str


class AddSourceRequest(BaseModel):
    source_id: int


@router.get("", response_model=list[GroupResponse])
async def list_groups(
    service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> list[GroupResponse]:
    groups = await service.list_groups_with_count()
    return [
        GroupResponse(
            id=g["id"],
            name=g["name"],
            member_count=g["member_count"],
            created_at=g["created_at"].isoformat(),
            updated_at=g["updated_at"].isoformat(),
        )
        for g in groups
    ]


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: GroupCreate,
    service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> GroupResponse:
    try:
        group = await service.create_group(name=data.name)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return GroupResponse(
        id=group.id,
        name=group.name,
        member_count=0,
        created_at=group.created_at.isoformat(),
        updated_at=group.updated_at.isoformat(),
    )


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    data: GroupUpdate,
    service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> GroupResponse:
    try:
        group = await service.update_group(
            group_id,
            **{k: v for k, v in data.model_dump().items() if v is not None},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return GroupResponse(
        id=group.id,
        name=group.name,
        created_at=group.created_at.isoformat(),
        updated_at=group.updated_at.isoformat(),
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> None:
    try:
        await service.delete_group(group_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{group_id}/sources")
async def get_group_sources(
    group_id: int,
    service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> list[dict]:
    sources = await service.get_group_sources(group_id)
    return [
        {
            "id": s.id,
            "name": s.name,
            "url": s.url,
            "is_active": s.is_active,
            "last_fetched_at": to_iso_string(s.last_fetched_at),
            "last_error": s.last_error,
            "created_at": to_iso_string(s.created_at) or "",
            "updated_at": to_iso_string(s.updated_at) or "",
        }
        for s in sources
    ]


@router.post("/{group_id}/sources")
async def add_source_to_group(
    group_id: int,
    data: AddSourceRequest,
    service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> dict:
    try:
        await service.add_source_to_group(group_id, data.source_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Source added to group"}


@router.delete(
    "/{group_id}/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_source_from_group(
    group_id: int,
    source_id: int,
    service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> None:
    try:
        await service.remove_source_from_group(group_id, source_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
