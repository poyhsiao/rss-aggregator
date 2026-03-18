"""Rate limiting service using sliding window algorithm."""

import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List


class RateLimiter:
    """In-memory rate limiter using sliding window algorithm."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in the window.
            window_seconds: Time window in seconds.
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str) -> bool:
        """Check if a request is allowed for the given key.

        Args:
            key: The key to check (e.g., API key).

        Returns:
            True if the request is allowed, False if rate limited.
        """
        with self._lock:
            now = time.time()
            window_start = now - self.window_seconds

            self._requests[key] = [
                req_time
                for req_time in self._requests[key]
                if req_time > window_start
            ]

            if len(self._requests[key]) >= self.max_requests:
                return False

            self._requests[key].append(now)
            return True

    def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key.

        Args:
            key: The key to check.

        Returns:
            Number of remaining requests in the current window.
        """
        with self._lock:
            now = time.time()
            window_start = now - self.window_seconds

            valid_requests = [
                req_time
                for req_time in self._requests.get(key, [])
                if req_time > window_start
            ]

            return max(0, self.max_requests - len(valid_requests))

    def get_reset_time(self, key: str) -> float:
        """Get seconds until rate limit resets.

        Args:
            key: The key to check.

        Returns:
            Seconds until the rate limit window resets.
        """
        with self._lock:
            requests = self._requests.get(key, [])
            if not requests:
                return 0.0

            oldest = min(requests)
            return max(0.0, oldest + self.window_seconds - time.time())