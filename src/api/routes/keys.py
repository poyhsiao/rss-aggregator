"""API key management routes."""

import re
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session, require_api_key
from src.models import APIKey

router = APIRouter(prefix="/keys", tags=["api-keys"])

KEY_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
MIN_KEY_LENGTH = 16
MAX_KEY_LENGTH = 255


class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""

    name: str | None = None
    key: str | None = None

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str | None) -> str | None:
        if v is None:
            return v

        if len(v) < MIN_KEY_LENGTH:
            raise ValueError(f"Key must be at least {MIN_KEY_LENGTH} characters")
        if len(v) > MAX_KEY_LENGTH:
            raise ValueError(f"Key must be at most {MAX_KEY_LENGTH} characters")
        if not KEY_PATTERN.match(v):
            raise ValueError("Key can only contain letters, numbers, hyphens, and underscores")

        return v


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
    if data.key:
        result = await session.execute(
            select(APIKey).where(APIKey.key == data.key)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Key already exists")
        key = data.key
    else:
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