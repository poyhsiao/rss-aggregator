from pydantic import BaseModel, Field


class HistoryItem(BaseModel):
    id: int
    source_id: int
    source: str
    title: str
    link: str
    description: str
    published_at: str | None
    fetched_at: str | None
    source_groups: list[dict] = []


class PaginationInfo(BaseModel):
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    total_items: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    pagination: PaginationInfo


class HistoryBatch(BaseModel):
    id: int
    name: str | None = None
    items_count: int
    sources: list[str]
    created_at: str
    latest_fetched_at: str | None = None
    latest_published_at: str | None = None
    groups: list[dict] = []


class UpdateBatchNameRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=500, description="Batch display name")


class DeleteBatchResponse(BaseModel):
    success: bool = Field(..., description="Whether the deletion was successful")


class DeleteHistoryResponse(BaseModel):
    success: bool = Field(..., description="Whether the deletion was successful")
    deleted_count: int = Field(..., ge=0, description="Number of items deleted")


class HistoryBatchesResponse(BaseModel):
    batches: list[HistoryBatch]
    total_batches: int
    total_items: int