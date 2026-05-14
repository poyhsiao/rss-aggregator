from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from src.api.deps import get_app_settings, get_schedule_service, require_api_key
from src.models.app_settings import AppSettings
from src.services.source_group_schedule_service import (
    SourceGroupScheduleService,
)
from src.utils.time import to_iso_string

router = APIRouter(prefix="/source-groups/{group_id}/schedules", tags=["schedules"])


async def _require_schedule_enabled(settings: AppSettings = Depends(get_app_settings)) -> None:
    if not settings.schedule_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="定時更新功能已停用")


class ScheduleCreate(BaseModel):
    cron_expression: str


class ScheduleUpdate(BaseModel):
    cron_expression: str


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int
    cron_expression: str
    is_enabled: bool
    next_run_at: str | None
    created_at: str
    updated_at: str


@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(
    group_id: int,
    service: SourceGroupScheduleService = Depends(get_schedule_service),
    _: str = Depends(require_api_key),
) -> list[ScheduleResponse]:
    schedules = await service.list_schedules(group_id)
    return [
        ScheduleResponse(
            id=s.id,
            group_id=s.group_id,
            cron_expression=s.cron_expression,
            is_enabled=s.is_enabled,
            next_run_at=to_iso_string(s.next_run_at),
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
        )
        for s in schedules
    ]


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(_require_schedule_enabled)])
async def create_schedule(
    group_id: int,
    data: ScheduleCreate,
    service: SourceGroupScheduleService = Depends(get_schedule_service),
    _: str = Depends(require_api_key),
) -> ScheduleResponse:
    try:
        schedule = await service.create_schedule(
            group_id=group_id,
            cron_expression=data.cron_expression,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return ScheduleResponse(
        id=schedule.id,
        group_id=schedule.group_id,
        cron_expression=schedule.cron_expression,
        is_enabled=schedule.is_enabled,
        next_run_at=to_iso_string(schedule.next_run_at),
        created_at=schedule.created_at.isoformat(),
        updated_at=schedule.updated_at.isoformat(),
    )


@router.put("/{schedule_id}", response_model=ScheduleResponse, dependencies=[Depends(_require_schedule_enabled)])
async def update_schedule(
    group_id: int,
    schedule_id: int,
    data: ScheduleUpdate,
    service: SourceGroupScheduleService = Depends(get_schedule_service),
    _: str = Depends(require_api_key),
) -> ScheduleResponse:
    try:
        schedule = await service.update_schedule(
            schedule_id=schedule_id,
            cron_expression=data.cron_expression,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404 if "not found" in str(e) else 400,
            detail=str(e),
        )
    
    return ScheduleResponse(
        id=schedule.id,
        group_id=schedule.group_id,
        cron_expression=schedule.cron_expression,
        is_enabled=schedule.is_enabled,
        next_run_at=to_iso_string(schedule.next_run_at),
        created_at=schedule.created_at.isoformat(),
        updated_at=schedule.updated_at.isoformat(),
    )


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(_require_schedule_enabled)])
async def delete_schedule(
    group_id: int,
    schedule_id: int,
    service: SourceGroupScheduleService = Depends(get_schedule_service),
    _: str = Depends(require_api_key),
) -> None:
    try:
        await service.delete_schedule(schedule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{schedule_id}/toggle", response_model=ScheduleResponse)
async def toggle_schedule(
    group_id: int,
    schedule_id: int,
    service: SourceGroupScheduleService = Depends(get_schedule_service),
    _: str = Depends(require_api_key),
) -> ScheduleResponse:
    try:
        schedule = await service.toggle_schedule(schedule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return ScheduleResponse(
        id=schedule.id,
        group_id=schedule.group_id,
        cron_expression=schedule.cron_expression,
        is_enabled=schedule.is_enabled,
        next_run_at=to_iso_string(schedule.next_run_at),
        created_at=schedule.created_at.isoformat(),
        updated_at=schedule.updated_at.isoformat(),
    )