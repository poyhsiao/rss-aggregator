"""API key management routes."""

import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session, require_api_key
from src.models import APIKey

router = APIRouter(prefix="/keys", tags=["api-keys"])


class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""

    name: str | None = None


class APIKeyResponse(BaseModel):
    """Schema for API key response."""

    id: int
    key: str
    name: str | None
    is_active: bool

    class Config:
        from_attributes = True


@router.get("", response_model=list[APIKeyResponse])
async def list_keys(
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_api_key),
) -> list[APIKeyResponse]:
    """List all API keys."""
    result = await session.execute(
        select(APIKey).where(APIKey.deleted_at.is_(None))
    )
    keys = list(result.scalars().all())
    return [APIKeyResponse(id=k.id, key=k.key, name=k.name, is_active=k.is_active) for k in keys]


@router.post("", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_key(
    data: APIKeyCreate,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_api_key),
) -> APIKeyResponse:
    """Create a new API key."""
    key = secrets.token_urlsafe(32)
    api_key = APIKey(key=key, name=data.name)
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)

    return APIKeyResponse(
        id=api_key.id,
        key=api_key.key,
        name=api_key.name,
        is_active=api_key.is_active,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_key(
    key_id: int,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_api_key),
) -> None:
    """Delete an API key."""
    result = await session.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.deleted_at.is_(None))
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key.soft_delete()
    await session.commit()