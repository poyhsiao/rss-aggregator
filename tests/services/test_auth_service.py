"""Tests for AuthService."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import APIKey
from src.services.auth_service import AuthService


@pytest_asyncio.fixture
async def auth_service(db_session: AsyncSession) -> AuthService:
    """Create AuthService instance."""
    return AuthService(db_session)


@pytest_asyncio.fixture
async def test_api_key(db_session: AsyncSession) -> APIKey:
    """Create a test API key."""
    api_key = APIKey(key="test-key-12345", name="Test Key")
    db_session.add(api_key)
    await db_session.commit()
    return api_key


@pytest.mark.asyncio
async def test_validate_key_returns_true_for_valid_key(
    auth_service: AuthService, test_api_key: APIKey
):
    """Test that validate_key returns True for valid key."""
    result = await auth_service.validate_key("test-key-12345")
    assert result is True


@pytest.mark.asyncio
async def test_validate_key_returns_false_for_invalid_key(
    auth_service: AuthService,
):
    """Test that validate_key returns False for invalid key."""
    result = await auth_service.validate_key("invalid-key")
    assert result is False


@pytest.mark.asyncio
async def test_validate_key_returns_false_for_deleted_key(
    auth_service: AuthService, db_session: AsyncSession, test_api_key: APIKey
):
    """Test that validate_key returns False for deleted key."""
    test_api_key.soft_delete()
    await db_session.commit()

    result = await auth_service.validate_key("test-key-12345")
    assert result is False


@pytest.mark.asyncio
async def test_validate_key_returns_false_for_inactive_key(
    auth_service: AuthService, db_session: AsyncSession, test_api_key: APIKey
):
    """Test that validate_key returns False for inactive key."""
    test_api_key.is_active = False
    await db_session.commit()

    result = await auth_service.validate_key("test-key-12345")
    assert result is False