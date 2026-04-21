"""Source group management API routes."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from pydantic import BaseModel, ConfigDict

from src.api.deps import get_app_settings, get_scheduler, get_feed_service, get_source_group_service, require_api_key, require_share_links_enabled
from src.models.app_settings import AppSettings
from src.services.feed_service import FeedService
from src.services.source_group_service import SourceGroupService
from src.utils.time import to_iso_string

router = APIRouter(prefix="/source-groups", tags=["source-groups"])


async def _require_group_enabled(settings: AppSettings = Depends(get_app_settings)) -> None:
    if not settings.group_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="群組功能已停用")


# Alias router for /groups prefix
groups_router = APIRouter(prefix="/groups", tags=["groups"])


class GroupCreate(BaseModel):
    name: str


class GroupUpdate(BaseModel):
    name: str | None = None


class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    member_count: int = 0
    schedule_count: int = 0
    created_at: str
    updated_at: str


class AddSourceRequest(BaseModel):
    source_id: int


@router.get("", response_model=list[GroupResponse], dependencies=[Depends(_require_group_enabled)])
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
            schedule_count=g.get("schedule_count", 0),
            created_at=g["created_at"].isoformat(),
            updated_at=g["updated_at"].isoformat(),
        )
        for g in groups
    ]


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(_require_group_enabled)])
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
        schedule_count=0,
        created_at=group.created_at.isoformat(),
        updated_at=group.updated_at.isoformat(),
    )


@router.put("/{group_id}", response_model=GroupResponse, dependencies=[Depends(_require_group_enabled)])
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

    count_result = await service.list_groups_with_count()
    member_count = next(
        (g["member_count"] for g in count_result if g["id"] == group.id), 0
    )
    schedule_count = next(
        (g.get("schedule_count", 0) for g in count_result if g["id"] == group.id), 0
    )

    return GroupResponse(
        id=group.id,
        name=group.name,
        member_count=member_count,
        schedule_count=schedule_count,
        created_at=group.created_at.isoformat(),
        updated_at=group.updated_at.isoformat(),
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(_require_group_enabled)])
async def delete_group(
    group_id: int,
    service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> None:
    try:
        await service.delete_group(group_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{group_id}/sources", dependencies=[Depends(_require_group_enabled)])
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


@router.post("/{group_id}/sources", dependencies=[Depends(_require_group_enabled)])
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
    "/{group_id}/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(_require_group_enabled)]
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


@router.post("/{group_id}/refresh", dependencies=[Depends(_require_group_enabled)])
async def refresh_group_sources(
    group_id: int,
    scheduler=Depends(get_scheduler),
    service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> dict:
    """Trigger refresh for all sources in a group."""
    try:
        await service.get_group_sources(group_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    await scheduler.refresh_group(group_id)
    return {"message": "Group sources refresh triggered"}


# Groups router (alias for /groups prefix)
@groups_router.get("/{group_id}/{format}")
async def get_group_feed_by_format(
    group_id: int,
    format: str = Path(
        ...,
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
    group_service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
    __: None = Depends(require_share_links_enabled),
) -> Response:
    """Get feed for a specific group by format path parameter.

    Returns RSS, JSON, or Markdown based on the format path parameter.

    Path params:
    - group_id: Group ID
    - format: Output format ('rss', 'json', or 'markdown')

    Query params:
    - sort_by: Sort field ('published_at' or 'source')
    - sort_order: Sort direction ('asc' or 'desc')
    - valid_time: Time range in hours
    - keywords: Keywords for filtering (semicolon-separated)
    """
    # Check if group exists
    sources = await group_service.get_group_sources(group_id)
    if not sources:
        raise HTTPException(status_code=404, detail="Group not found or has no sources")

    content, content_type = await feed_service.get_formatted_feed(
        format=format,
        sort_by=sort_by,
        sort_order=sort_order,
        valid_time=valid_time,
        keywords=keywords,
        group_id=group_id,
    )
    return Response(content=content, media_type=content_type)
