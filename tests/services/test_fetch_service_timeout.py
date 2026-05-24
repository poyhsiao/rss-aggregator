# tests/services/test_fetch_service_timeout.py
import pytest
import asyncio
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.fetch_service import FetchService


@pytest.mark.asyncio
async def test_fetch_catches_asyncio_timeout_error():
    """FetchService should catch asyncio.TimeoutError, not just httpx.HTTPError."""
    service = FetchService(session=MagicMock())

    # Mock httpx.AsyncClient to raise asyncio.TimeoutError
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(
            side_effect=asyncio.TimeoutError("Connection timeout")
        )
        mock_client_class.return_value = mock_client

        source = MagicMock()
        source.id = 1
        source.url = "http://example.com/feed"
        source.name = "Test"

        # Should NOT raise, should return None
        result = await service._fetch_with_retry(source.id, source.url)
        assert result is None


@pytest.mark.asyncio
async def test_fetch_catches_httpx_http_error():
    """FetchService should still catch httpx.HTTPError."""
    service = FetchService(session=MagicMock())

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(
            side_effect=httpx.HTTPError("Network error")
        )
        mock_client_class.return_value = mock_client

        source = MagicMock()
        source.id = 1
        source.url = "http://example.com/feed"

        result = await service._fetch_with_retry(source.id, source.url)
        assert result is None