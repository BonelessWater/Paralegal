"""
Simple in-memory cache with TTL support
Optimized for API response caching
"""

import time
import asyncio
from typing import Any, Optional, Callable, Dict
from functools import wraps
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

class CacheEntry:
    """Single cache entry with expiration"""

    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.expires_at = time.time() + ttl

    def is_expired(self) -> bool:
        """Check if entry has expired"""
        return time.time() > self.expires_at

class SimpleCache:
    """
    Simple in-memory cache with TTL support

    Example:
        cache = SimpleCache(default_ttl=300)
        cache.set("key", "value", ttl=60)
        value = cache.get("key")
    """

    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """
        Initialize cache

        Args:
            default_ttl: Default time-to-live in seconds
            max_size: Maximum number of entries
        """
        self._cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._lock = asyncio.Lock()

    def _make_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        entry = self._cache.get(key)

        if entry is None:
            return None

        if entry.is_expired():
            del self._cache[key]
            return None

        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        if len(self._cache) >= self.max_size:
            # Remove oldest entries if cache is full
            self._evict_oldest()

        ttl = ttl or self.default_ttl
        self._cache[key] = CacheEntry(value, ttl)

    def delete(self, key: str) -> None:
        """Delete key from cache"""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()

    def _evict_oldest(self, count: int = 10) -> None:
        """Evict oldest cache entries"""
        # Remove expired entries first
        expired = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired:
            del self._cache[key]

        # If still over limit, remove oldest
        if len(self._cache) >= self.max_size:
            sorted_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k].expires_at
            )
            for key in sorted_keys[:count]:
                del self._cache[key]

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self._cache)
        expired_entries = sum(1 for v in self._cache.values() if v.is_expired())

        return {
            'total_entries': total_entries,
            'active_entries': total_entries - expired_entries,
            'expired_entries': expired_entries,
            'max_size': self.max_size,
            'utilization': f"{(total_entries / self.max_size * 100):.1f}%"
        }

def cached(ttl: int = 300, cache_instance: Optional[SimpleCache] = None):
    """
    Decorator to cache function results

    Args:
        ttl: Time-to-live in seconds
        cache_instance: Cache instance to use (creates new if None)

    Example:
        @cached(ttl=60)
        def expensive_function(arg1, arg2):
            # expensive computation
            return result
    """
    if cache_instance is None:
        cache_instance = SimpleCache(default_ttl=ttl)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_instance._make_key(func.__name__, *args, **kwargs)

            # Try to get from cache
            result = cache_instance.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result

            # Call function and cache result
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            cache_instance.set(cache_key, result, ttl)

            return result

        # Attach cache management methods
        wrapper.cache_clear = lambda: cache_instance.clear()
        wrapper.cache_stats = lambda: cache_instance.stats()

        return wrapper
    return decorator

def async_cached(ttl: int = 300, cache_instance: Optional[SimpleCache] = None):
    """
    Decorator to cache async function results

    Args:
        ttl: Time-to-live in seconds
        cache_instance: Cache instance to use (creates new if None)

    Example:
        @async_cached(ttl=60)
        async def expensive_async_function(arg1, arg2):
            # expensive async computation
            return result
    """
    if cache_instance is None:
        cache_instance = SimpleCache(default_ttl=ttl)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_instance._make_key(func.__name__, *args, **kwargs)

            # Try to get from cache
            result = cache_instance.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result

            # Call function and cache result
            logger.debug(f"Cache miss for {func.__name__}")
            result = await func(*args, **kwargs)
            cache_instance.set(cache_key, result, ttl)

            return result

        # Attach cache management methods
        wrapper.cache_clear = lambda: cache_instance.clear()
        wrapper.cache_stats = lambda: cache_instance.stats()

        return wrapper
    return decorator

# Global cache instance
global_cache = SimpleCache(default_ttl=300, max_size=1000)
