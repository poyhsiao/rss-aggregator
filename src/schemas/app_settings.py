"""Pydantic schemas for app settings."""

from pydantic import BaseModel, ConfigDict, Field


class AppSettingsResponse(BaseModel):
    """Schema for reading app settings."""
    model_config = ConfigDict(from_attributes=True)
    group_enabled: bool
    schedule_enabled: bool
    share_enabled: bool


class AppSettingsUpdate(BaseModel):
    """Schema for updating app settings (partial update supported)."""
    group_enabled: bool | None = Field(default=None)
    schedule_enabled: bool | None = Field(default=None)
    share_enabled: bool | None = Field(default=None)
