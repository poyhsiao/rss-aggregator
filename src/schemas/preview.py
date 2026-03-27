from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FetchPreviewRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)


class PreviewContentRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)
    markdown_content: str = Field(..., min_length=1)
    title: str | None = Field(None, max_length=500)


class PreviewContentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    url_hash: str
    markdown_content: str
    title: str | None
    created_at: datetime
    updated_at: datetime