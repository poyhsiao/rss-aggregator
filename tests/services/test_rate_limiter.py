"""Tests for RateLimiter."""

import asyncio

import pytest

from src.services.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_allows_requests_within_limit():
    """Test that requests within limit are allowed."""
    limiter = RateLimiter(max_requests=5, window_seconds=60)

    for _ in range(5):
        assert await limiter.is_allowed("test-key") is True


@pytest.mark.asyncio
async def test_rate_limiter_blocks_requests_over_limit():
    """Test that requests over limit are blocked."""
    limiter = RateLimiter(max_requests=3, window_seconds=60)

    for _ in range(3):
        await limiter.is_allowed("test-key")

    assert await limiter.is_allowed("test-key") is False


@pytest.mark.asyncio
async def test_rate_limiter_get_remaining():
    """Test that get_remaining returns correct count."""
    limiter = RateLimiter(max_requests=5, window_seconds=60)

    assert await limiter.get_remaining("test-key") == 5
    await limiter.is_allowed("test-key")
    assert await limiter.get_remaining("test-key") == 4


@pytest.mark.asyncio
async def test_rate_limiter_different_keys_independent():
    """Test that different keys have independent limits."""
    limiter = RateLimiter(max_requests=2, window_seconds=60)

    await limiter.is_allowed("key-1")
    await limiter.is_allowed("key-1")
    assert await limiter.is_allowed("key-1") is False

    assert await limiter.is_allowed("key-2") is True
    assert await limiter.is_allowed("key-2") is True


@pytest.mark.asyncio
async def test_rate_limiter_window_expires():
    """Test that rate limit resets after window expires."""
    limiter = RateLimiter(max_requests=2, window_seconds=1)

    await limiter.is_allowed("test-key")
    await limiter.is_allowed("test-key")
    assert await limiter.is_allowed("test-key") is False

    await asyncio.sleep(1.1)
    assert await limiter.is_allowed("test-key") is True