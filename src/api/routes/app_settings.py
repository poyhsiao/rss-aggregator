"""App settings API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session, require_api_key
from src.models.app_settings import AppSettings
from src.schemas.app_settings import AppSettingsResponse, AppSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


async def _get_or_create_settings(session: AsyncSession) -> AppSettings:
    """Return the singleton AppSettings record, creating it if absent."""
    result = await session.execute(select(AppSettings))
    settings = result.scalars().first()
    if settings is None:
        settings = AppSettings()
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
    return settings


@router.get("", response_model=AppSettingsResponse)
async def get_app_settings(
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_api_key),
) -> AppSettingsResponse:
    """Get current global feature toggle settings."""
    settings = await _get_or_create_settings(session)
    return AppSettingsResponse.model_validate(settings)


@router.put("", response_model=AppSettingsResponse)
async def update_app_settings(
    data: AppSettingsUpdate,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_api_key),
) -> AppSettingsResponse:
    """Update global feature toggle settings (partial update supported)."""
    settings = await _get_or_create_settings(session)
    patch = data.model_dump(exclude_unset=True)
    for key, value in patch.items():
        setattr(settings, key, value)
    await session.commit()
    await session.refresh(settings)
    return AppSettingsResponse.model_validate(settings)
