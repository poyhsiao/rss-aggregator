"""Authentication service for API key validation."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import APIKey


class AuthService:
    """Service for validating API keys."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def validate_key(self, api_key: str) -> bool:
        """Validate an API key.

        Args:
            api_key: The API key to validate.

        Returns:
            True if the key is valid, False otherwise.
        """
        result = await self.session.execute(
            select(APIKey).where(
                APIKey.key == api_key,
                APIKey.is_active == True,
                APIKey.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none() is not None