"""
Retry logic with exponential backoff for external API calls.
"""

import asyncio
import random
from typing import TypeVar, Callable, Any, Optional, Awaitable
from functools import wraps

from src.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 32.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    backoff_factor: float = 1.0,
):
    """
    Decorator for retrying async functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delay
        backoff_factor: Factor to multiply backoff by
        
    Example:
        @retry(max_attempts=3, initial_delay=1.0)
        async def fetch_data():
            return await api.get_data()
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            attempt = 0
            delay = initial_delay

            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    attempt += 1

                    if attempt >= max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    actual_delay = min(
                        delay * (exponential_base ** (attempt - 1)) * backoff_factor,
                        max_delay
                    )

                    # Add jitter if enabled
                    if jitter:
                        actual_delay += random.uniform(0, actual_delay * 0.1)

                    logger.warning(
                        f"{func.__name__} attempt {attempt} failed: {e}. "
                        f"Retrying in {actual_delay:.2f}s..."
                    )

                    await asyncio.sleep(actual_delay)

            return None  # Should not reach here

        return wrapper

    return decorator


class RetryConfig:
    """Configuration for retry behavior"""

    # API call defaults
    STOCK_API_MAX_ATTEMPTS = 3
    STOCK_API_INITIAL_DELAY = 1.0
    STOCK_API_MAX_DELAY = 10.0

    NEWS_API_MAX_ATTEMPTS = 3
    NEWS_API_INITIAL_DELAY = 0.5
    NEWS_API_MAX_DELAY = 5.0

    INDEX_API_MAX_ATTEMPTS = 3
    INDEX_API_INITIAL_DELAY = 1.0
    INDEX_API_MAX_DELAY = 10.0

    # Database defaults
    DB_MAX_ATTEMPTS = 3
    DB_INITIAL_DELAY = 0.1
    DB_MAX_DELAY = 2.0
