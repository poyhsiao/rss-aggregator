"""Health check endpoint."""

from fastapi import APIRouter

from src.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        Status and configuration info.
    """
    return {
        "status": "ok",
        "require_api_key": settings.require_api_key,
    }