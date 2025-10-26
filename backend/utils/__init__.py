"""
Utility modules for Paralegal AI Backend

Available utilities:
- retry: Retry decorators with exponential backoff
- cache: Simple caching system with TTL support
"""

from .retry import (
    retry_with_backoff,
    async_retry_with_backoff,
    retry_async,
    RetryError,
)

from .cache import (
    SimpleCache,
    cached,
    async_cached,
    global_cache,
)

__all__ = [
    # Retry utilities
    "retry_with_backoff",
    "async_retry_with_backoff",
    "retry_async",
    "RetryError",
    # Cache utilities
    "SimpleCache",
    "cached",
    "async_cached",
    "global_cache",
]
