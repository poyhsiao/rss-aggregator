import pytest
import asyncio
from src.services.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_uses_async_lock():
    """RateLimiter should use asyncio.Lock, not threading.Lock."""
    limiter = RateLimiter(max_requests=10, window_seconds=60)
    # Verify the lock is an asyncio.Lock
    import asyncio
    assert isinstance(limiter._lock, asyncio.Lock), \
        f"Expected asyncio.Lock, got {type(limiter._lock)}"


@pytest.mark.asyncio
async def test_rate_limiter_concurrent_access():
    """RateLimiter should handle concurrent async access correctly."""
    limiter = RateLimiter(max_requests=5, window_seconds=60)
    key = "test-key"

    # Simulate concurrent requests
    async def check_and_record():
        result = await limiter.is_allowed(key)
        return result

    # Run 10 concurrent checks
    results = await asyncio.gather(*[check_and_record() for _ in range(10)])

    # Should allow exactly 5 requests
    allowed_count = sum(1 for r in results if r is True)
    assert allowed_count == 5, f"Expected 5 allowed, got {allowed_count}"