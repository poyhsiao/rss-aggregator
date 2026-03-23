"""Pydantic schemas for history API."""

from pydantic import BaseModel, Field


class HistoryItem(BaseModel):
    """Schema for a history feed item."""

    id: int
    source_id: int
    source: str
    title: str
    link: str
    description: str
    published_at: str | None
    fetched_at: str | None


class PaginationInfo(BaseModel):
    """Schema for pagination info."""

    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    total_items: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)


class HistoryResponse(BaseModel):
    """Schema for history API response."""

    items: list[HistoryItem]
    pagination: PaginationInfo
