from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.api.deps import get_preview_service
from src.schemas.preview import (
    FetchPreviewRequest,
    PreviewContentRequest,
    PreviewContentResponse,
)
from src.services.preview_service import PreviewService

router = APIRouter(prefix="/previews", tags=["previews"])


@router.post(
    "/fetch",
    response_model=PreviewContentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def fetch_and_cache_preview(
    request: FetchPreviewRequest,
    preview_service: PreviewService = Depends(get_preview_service),
) -> PreviewContentResponse:
    result = await preview_service.fetch_and_cache(request.url)
    return PreviewContentResponse.model_validate(result)


@router.get(
    "/{url_hash}",
    response_model=PreviewContentResponse,
)
async def get_preview_by_hash(
    url_hash: str = Path(..., min_length=64, max_length=64),
    preview_service: PreviewService = Depends(get_preview_service),
) -> PreviewContentResponse:
    result = await preview_service.get_by_url_hash(url_hash)
    if not result:
        raise HTTPException(status_code=404, detail="Preview not found")
    return PreviewContentResponse.model_validate(result)


@router.get(
    "",
    response_model=PreviewContentResponse,
)
async def get_preview_by_url(
    url: str = Query(..., min_length=1, max_length=2048),
    preview_service: PreviewService = Depends(get_preview_service),
) -> PreviewContentResponse:
    result = await preview_service.get_by_url(url)
    if not result:
        raise HTTPException(status_code=404, detail="Preview not found")
    return PreviewContentResponse.model_validate(result)


@router.post(
    "",
    response_model=PreviewContentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_preview(
    request: PreviewContentRequest,
    preview_service: PreviewService = Depends(get_preview_service),
) -> PreviewContentResponse:
    result = await preview_service.upsert(
        url=request.url,
        markdown_content=request.markdown_content,
        title=request.title,
    )
    return PreviewContentResponse.model_validate(result)