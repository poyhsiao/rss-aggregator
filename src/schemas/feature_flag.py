"""Feature flag schemas."""

from typing import Optional

from pydantic import BaseModel


class FeatureFlagsResponse(BaseModel):
    """Response schema for feature flags."""

    groups_enabled: bool = True
    group_schedules_enabled: bool = True
    source_group_schedules_enabled: bool = True


class FeatureFlagsUpdate(BaseModel):
    """Request schema for updating feature flags."""

    groups_enabled: Optional[bool] = None
    group_schedules_enabled: Optional[bool] = None
    source_group_schedules_enabled: Optional[bool] = None