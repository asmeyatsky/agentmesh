"""
Retry Policy with Exponential Backoff

Handles transient failures through intelligent retry logic with:
- Exponential backoff to reduce load on failing services
- Jitter to prevent thundering herd
- Configurable retry strategies
- Observability through logging and metrics
"""

import asyncio
import random
import logging
from typing import Callable, TypeVar, Optional, Awaitable, Any, Type, Tuple


T = TypeVar('T')


class RetryException(Exception):
    """Exception raised when all retry attempts fail"""
    pass


class RetryPolicy:
    """
    Configurable retry policy with backoff strategies.

    Supports:
    - Exponential backoff
    - Jitter to prevent synchronized retries
    - Configurable max attempts and delays
    - Selective exception handling
    """

    def __init__(self,
                 max_attempts: int = 3,
                 initial_delay_ms: int = 100,
                 max_delay_ms: int = 10000,
                 exponential_base: float = 2.0,
                 jitter: bool = True,
                 jitter_percent: float = 20.0):
        """
        Initialize retry policy

        Args:
            max_attempts: Maximum retry attempts (1 = no retry)
            initial_delay_ms: Initial delay between retries
            max_delay_ms: Maximum delay between retries
            exponential_base: Base for exponential backoff
            jitter: Add randomness to delays (prevents thundering herd)
            jitter_percent: Jitter magnitude (percentage of delay)
        """
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        self.max_attempts = max_attempts
        self.initial_delay_ms = initial_delay_ms
        self.max_delay_ms = max_delay_ms
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.jitter_percent = jitter_percent

        self.logger = logging.getLogger(__name__)

    async def execute(self,
                     func: Callable[..., Awaitable[T]],
                     *args,
                     retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
                     **kwargs) -> T:
        """
        Execute async function with retry policy.

        Args:
            func: Async function to execute
            args: Function positional arguments
            retryable_exceptions: Tuple of exception types to retry on
            kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            RetryException: When all attempts fail
        """
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except retryable_exceptions as e:
                last_exception = e

                if attempt < self.max_attempts:
                    delay_ms = self._calculate_delay(attempt)
                    self.logger.warning(
                        f"Attempt {attempt}/{self.max_attempts} failed for "
                        f"{func.__name__}: {str(e)[:100]}. "
                        f"Retrying in {delay_ms:.0f}ms..."
                    )
                    await asyncio.sleep(delay_ms / 1000)
                else:
                    self.logger.error(
                        f"All {self.max_attempts} attempts failed for {func.__name__}: {str(e)}"
                    )

        raise RetryException(
            f"Failed after {self.max_attempts} attempts: {str(last_exception)}"
        ) from last_exception

    def execute_sync(self,
                    func: Callable[..., T],
                    *args,
                    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
                    **kwargs) -> T:
        """
        Execute synchronous function with retry policy.

        Args:
            func: Sync function to execute
            args: Function positional arguments
            retryable_exceptions: Tuple of exception types to retry on
            kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            RetryException: When all attempts fail
        """
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except retryable_exceptions as e:
                last_exception = e

                if attempt < self.max_attempts:
                    delay_ms = self._calculate_delay(attempt)
                    self.logger.warning(
                        f"Attempt {attempt}/{self.max_attempts} failed for "
                        f"{func.__name__}: {str(e)[:100]}. "
                        f"Retrying in {delay_ms:.0f}ms..."
                    )
                    import time
                    time.sleep(delay_ms / 1000)
                else:
                    self.logger.error(
                        f"All {self.max_attempts} attempts failed for {func.__name__}: {str(e)}"
                    )

        raise RetryException(
            f"Failed after {self.max_attempts} attempts: {str(last_exception)}"
        ) from last_exception

    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt using exponential backoff with jitter.

        Formula:
            delay = min(initial * base^(attempt-1), max)
            if jitter: delay += random(±jitter%)

        Args:
            attempt: Current attempt number (1-indexed)

        Returns:
            Delay in milliseconds
        """
        # Calculate exponential backoff
        exponential_delay = self.initial_delay_ms * (self.exponential_base ** (attempt - 1))
        capped_delay = min(exponential_delay, self.max_delay_ms)

        # Add jitter if enabled
        if self.jitter:
            # Calculate jitter as percentage of delay
            jitter_magnitude = capped_delay * (self.jitter_percent / 100) * (2 * random.random() - 1)
            return capped_delay + jitter_magnitude

        return float(capped_delay)

    @staticmethod
    def for_database() -> 'RetryPolicy':
        """Create retry policy optimized for database operations"""
        return RetryPolicy(
            max_attempts=3,
            initial_delay_ms=50,
            max_delay_ms=2000,
            exponential_base=2.0,
            jitter=True
        )

    @staticmethod
    def for_external_api() -> 'RetryPolicy':
        """Create retry policy optimized for external API calls"""
        return RetryPolicy(
            max_attempts=4,
            initial_delay_ms=200,
            max_delay_ms=5000,
            exponential_base=2.0,
            jitter=True
        )

    @staticmethod
    def for_message_broker() -> 'RetryPolicy':
        """Create retry policy optimized for message broker operations"""
        return RetryPolicy(
            max_attempts=5,
            initial_delay_ms=100,
            max_delay_ms=10000,
            exponential_base=2.0,
            jitter=True
        )

    @staticmethod
    def aggressive() -> 'RetryPolicy':
        """Create aggressive retry policy (quick retries)"""
        return RetryPolicy(
            max_attempts=3,
            initial_delay_ms=10,
            max_delay_ms=500,
            exponential_base=1.5,
            jitter=False
        )

    @staticmethod
    def conservative() -> 'RetryPolicy':
        """Create conservative retry policy (long delays)"""
        return RetryPolicy(
            max_attempts=3,
            initial_delay_ms=500,
            max_delay_ms=30000,
            exponential_base=3.0,
            jitter=True
        )
