"""
Retry utilities with exponential backoff
Provides decorators and functions for resilient API calls
"""

import asyncio
import time
import logging
from functools import wraps
from typing import Callable, TypeVar, Optional, Type, Tuple

logger = logging.getLogger(__name__)

T = TypeVar('T')

class RetryError(Exception):
    """Raised when all retry attempts are exhausted"""
    pass

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorator to retry a function with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback function called on each retry

    Example:
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        def fetch_data():
            return requests.get("https://api.example.com/data")
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise RetryError(
                            f"Failed after {max_retries} retries: {e}"
                        ) from e

                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )

                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {delay:.2f}s: {e}"
                    )

                    if on_retry:
                        on_retry(attempt, delay, e)

                    time.sleep(delay)

            # This should never be reached, but mypy needs it
            raise RetryError("Unexpected retry loop exit") from last_exception

        return wrapper
    return decorator

def async_retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Async decorator to retry a coroutine with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback function called on each retry

    Example:
        @async_retry_with_backoff(max_retries=3, base_delay=1.0)
        async def fetch_data():
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.example.com/data") as resp:
                    return await resp.json()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"Async function {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise RetryError(
                            f"Failed after {max_retries} retries: {e}"
                        ) from e

                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )

                    logger.warning(
                        f"Async function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {delay:.2f}s: {e}"
                    )

                    if on_retry:
                        if asyncio.iscoroutinefunction(on_retry):
                            await on_retry(attempt, delay, e)
                        else:
                            on_retry(attempt, delay, e)

                    await asyncio.sleep(delay)

            # This should never be reached, but mypy needs it
            raise RetryError("Unexpected retry loop exit") from last_exception

        return wrapper
    return decorator

# Convenience function for manual retries
async def retry_async(
    func: Callable[..., T],
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    **kwargs
) -> T:
    """
    Manually retry an async function with exponential backoff

    Example:
        result = await retry_async(
            fetch_data,
            url="https://api.example.com",
            max_retries=5,
            base_delay=2.0
        )
    """
    @async_retry_with_backoff(max_retries=max_retries, base_delay=base_delay)
    async def _wrapped():
        return await func(*args, **kwargs)

    return await _wrapped()
