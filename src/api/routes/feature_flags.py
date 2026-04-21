"""Feature flag management API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from src.api.deps import require_api_key
from src.models.feature_flag import FeatureFlag
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/feature-flags", tags=["feature-flags"])

VALID_FLAG_KEYS = {"feature_groups", "feature_schedules", "feature_share_links"}


class FeatureFlagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    enabled: bool
    created_at: str
    updated_at: str


class FlagUpdateRequest(BaseModel):
    key: str
    value: bool


async def get_flag(key: str, session: AsyncSession) -> FeatureFlag | None:
    result = await session.execute(select(FeatureFlag).where(FeatureFlag.key == key))
    return result.scalar_one_or_none()


async def ensure_default_flags(session: AsyncSession) -> None:
    for flag_key in VALID_FLAG_KEYS:
        flag = await get_flag(flag_key, session)
        if flag is None:
            session.add(FeatureFlag(key=flag_key, enabled=False))
    await session.commit()


@router.get("", response_model=list[FeatureFlagResponse])
async def list_feature_flags(
    session: AsyncSession = Depends(__import__("src.api.deps", fromlist=["get_session"]).get_session),
    _: str = Depends(require_api_key),
) -> list[FeatureFlagResponse]:
    await ensure_default_flags(session)
    result = await session.execute(select(FeatureFlag))
    flags = result.scalars().all()
    return [
        FeatureFlagResponse(
            key=f.key,
            enabled=f.enabled,
            created_at=f.created_at.isoformat(),
            updated_at=f.updated_at.isoformat(),
        )
        for f in flags
    ]


@router.patch("", response_model=FeatureFlagResponse)
async def update_feature_flag(
    data: FlagUpdateRequest,
    session: AsyncSession = Depends(__import__("src.api.deps", fromlist=["get_session"]).get_session),
    _: str = Depends(require_api_key),
) -> FeatureFlagResponse:
    if data.key not in VALID_FLAG_KEYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid flag name. Valid keys: {', '.join(sorted(VALID_FLAG_KEYS))}",
        )

    await ensure_default_flags(session)
    flag = await get_flag(data.key, session)
    if flag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flag '{data.key}' not found",
        )

    flag.enabled = data.value
    await session.commit()
    await session.refresh(flag)

    return FeatureFlagResponse(
        key=flag.key,
        enabled=flag.enabled,
        created_at=flag.created_at.isoformat(),
        updated_at=flag.updated_at.isoformat(),
    )