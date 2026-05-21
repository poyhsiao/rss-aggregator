"""Feature flags API routes."""


from fastapi import APIRouter, Depends

from src.api.deps import get_feature_flag_service, require_api_key
from src.schemas.feature_flag import FeatureFlagsResponse, FeatureFlagsUpdate
from src.services.feature_flag_service import FeatureFlagService

router = APIRouter(prefix="/feature-flags", tags=["feature-flags"])


@router.get("", response_model=FeatureFlagsResponse)
async def get_feature_flags(
    service: FeatureFlagService = Depends(get_feature_flag_service),
    _: str = Depends(require_api_key),
) -> FeatureFlagsResponse:
    """Get all feature flags.

    Returns:
        All feature flags with their boolean values.
    """
    flags = await service.get_all()
    return FeatureFlagsResponse(**flags)


@router.put("", response_model=FeatureFlagsResponse)
async def update_feature_flags(
    update: FeatureFlagsUpdate,
    service: FeatureFlagService = Depends(get_feature_flag_service),
    _: str = Depends(require_api_key),
) -> FeatureFlagsResponse:
    """Update one or more feature flags.

    Args:
        update: Feature flags to update.

    Returns:
        Updated feature flags.
    """
    flags_to_update = {}
    if update.groups_enabled is not None:
        flags_to_update["groups_enabled"] = update.groups_enabled
    if update.group_schedules_enabled is not None:
        flags_to_update["group_schedules_enabled"] = update.group_schedules_enabled
    if update.source_group_schedules_enabled is not None:
        flags_to_update["source_group_schedules_enabled"] = update.source_group_schedules_enabled

    if flags_to_update:
        await service.update_batch(flags_to_update)

    flags = await service.get_all()
    return FeatureFlagsResponse(**flags)