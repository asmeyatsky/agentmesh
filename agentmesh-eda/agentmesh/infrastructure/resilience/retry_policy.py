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
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, TypeVar, Optional, Awaitable, Any, Type, Tuple, List

T = TypeVar('T')


class RetryableError(Exception):
    """Exception that should trigger a retry"""
    pass


class NonRetryableError(Exception):
    """Exception that should NOT trigger a retry"""
    pass


class MaxRetriesExceededError(Exception):
    """Exception raised when all retry attempts fail"""

    def __init__(self, max_attempts: int, last_error: Exception, total_duration_ms: float):
        self.max_attempts = max_attempts
        self.last_error = last_error
        self.total_duration_ms = total_duration_ms
        super().__init__(f"max attempts ({max_attempts}) exceeded: {last_error}")


# Backward-compatible alias
RetryException = MaxRetriesExceededError


@dataclass
class RetryConfig:
    """Configuration for retry policy"""
    max_attempts: int = 3
    base_delay_ms: int = 100
    max_delay_ms: int = 30000
    backoff_multiplier: float = 2.0
    jitter_enabled: bool = True
    jitter_range_ms: int = 100
    retryable_exceptions: Optional[List[type]] = None
    non_retryable_exceptions: Optional[List[type]] = None

    _default_retryable = (ConnectionError, TimeoutError, OSError, RetryableError)
    _default_non_retryable = (ValueError, KeyError, TypeError, NonRetryableError)

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt using exponential backoff"""
        delay = self.base_delay_ms * (self.backoff_multiplier ** (attempt - 1))
        delay = min(delay, self.max_delay_ms)

        if self.jitter_enabled:
            jitter = random.uniform(-self.jitter_range_ms, self.jitter_range_ms)
            delay = max(0, delay + jitter)

        return delay

    def is_retryable_exception(self, exc: Exception) -> bool:
        """Determine if an exception should trigger a retry"""
        if self.retryable_exceptions is not None:
            # When custom retryable list is provided, use it exclusively
            if self.non_retryable_exceptions and isinstance(exc, tuple(self.non_retryable_exceptions)):
                return False
            return isinstance(exc, tuple(self.retryable_exceptions))

        # Default behavior: check non-retryable first, then retryable
        if isinstance(exc, tuple(self._default_non_retryable)):
            return False
        return isinstance(exc, tuple(self._default_retryable))


@dataclass
class RetryResult:
    """Result of a retry execution"""
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    attempts: int = 0
    total_duration_ms: float = 0.0


@dataclass
class RetryState:
    """State tracked during retry execution"""
    attempt: int
    last_error: Optional[Exception] = None
    total_delay_ms: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)

    def should_continue_retrying(self, config: RetryConfig) -> bool:
        """Determine if retrying should continue"""
        if self.attempt >= config.max_attempts:
            return False
        if self.last_error and not config.is_retryable_exception(self.last_error):
            return False
        return True


class RetryPolicy:
    """
    Configurable retry policy with backoff strategies.

    Supports:
    - Exponential backoff
    - Jitter to prevent synchronized retries
    - Configurable max attempts and delays
    - Selective exception handling
    - Progress callbacks
    - Statistics tracking
    """

    def __init__(self,
                 config: Optional[RetryConfig] = None,
                 max_attempts: int = 3,
                 initial_delay_ms: int = 100,
                 max_delay_ms: int = 10000,
                 exponential_base: float = 2.0,
                 jitter: bool = True,
                 jitter_percent: float = 20.0):
        if config:
            self.config = config
        else:
            self.config = RetryConfig(
                max_attempts=max_attempts,
                base_delay_ms=initial_delay_ms,
                max_delay_ms=max_delay_ms,
                backoff_multiplier=exponential_base,
                jitter_enabled=jitter,
                jitter_range_ms=int(initial_delay_ms * jitter_percent / 100),
            )

        self.logger = logging.getLogger(__name__)
        self._stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_attempts": 0,
            "max_attempts_reached": 0,
        }

    async def execute(self,
                      func: Callable,
                      *args,
                      timeout_ms: Optional[int] = None,
                      progress_callback: Optional[Callable] = None,
                      retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
                      **kwargs) -> RetryResult:
        """Execute function with retry policy, returning a RetryResult."""
        self._stats["total_executions"] += 1
        start_time = datetime.now()
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.config.max_attempts + 1):
            state = RetryState(attempt=attempt, last_error=last_exception)

            try:
                if asyncio.iscoroutinefunction(func):
                    if timeout_ms:
                        result = await asyncio.wait_for(
                            func(*args, **kwargs),
                            timeout=timeout_ms / 1000
                        )
                    else:
                        result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                elapsed = (datetime.now() - start_time).total_seconds() * 1000
                self._stats["successful_executions"] += 1
                self._stats["total_attempts"] += attempt
                if progress_callback:
                    progress_callback(RetryState(attempt=attempt, last_error=last_exception))
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempt,
                    total_duration_ms=elapsed,
                )

            except asyncio.TimeoutError as e:
                elapsed = (datetime.now() - start_time).total_seconds() * 1000
                self._stats["failed_executions"] += 1
                self._stats["total_attempts"] += attempt
                self._stats["max_attempts_reached"] += 1
                return RetryResult(
                    success=False,
                    error=TimeoutError(f"timeout after {timeout_ms}ms"),
                    attempts=attempt,
                    total_duration_ms=elapsed,
                )

            except Exception as e:
                last_exception = e

                # Check if we should retry
                should_retry = False
                if retryable_exceptions:
                    should_retry = isinstance(e, retryable_exceptions)
                else:
                    should_retry = self.config.is_retryable_exception(e)

                if not should_retry or attempt >= self.config.max_attempts:
                    elapsed = (datetime.now() - start_time).total_seconds() * 1000
                    self._stats["total_attempts"] += attempt
                    if attempt >= self.config.max_attempts and should_retry:
                        self._stats["max_attempts_reached"] += 1
                        self._stats["failed_executions"] += 1
                        return RetryResult(
                            success=False,
                            error=MaxRetriesExceededError(
                                max_attempts=self.config.max_attempts,
                                last_error=e,
                                total_duration_ms=elapsed,
                            ),
                            attempts=attempt,
                            total_duration_ms=elapsed,
                        )
                    else:
                        # Non-retryable error on first attempt
                        self._stats["failed_executions"] += 1
                        return RetryResult(
                            success=False,
                            error=e,
                            attempts=attempt,
                            total_duration_ms=elapsed,
                        )

                if progress_callback:
                    progress_callback(RetryState(attempt=attempt, last_error=e))

                # Calculate delay and wait
                delay_ms = self.config.calculate_delay(attempt)
                self.logger.warning(
                    f"Attempt {attempt}/{self.config.max_attempts} failed: "
                    f"{str(e)[:100]}. Retrying in {delay_ms:.0f}ms..."
                )
                await asyncio.sleep(delay_ms / 1000)

        # Should not reach here, but just in case
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        self._stats["failed_executions"] += 1
        return RetryResult(
            success=False,
            error=last_exception,
            attempts=self.config.max_attempts,
            total_duration_ms=elapsed,
        )

    def get_statistics(self) -> dict:
        """Get retry statistics"""
        total = self._stats["total_executions"]
        total_attempts = self._stats["total_attempts"]
        return {
            "total_executions": total,
            "successful_executions": self._stats["successful_executions"],
            "failed_executions": self._stats["failed_executions"],
            "average_attempts": total_attempts / total if total > 0 else 0.0,
            "max_attempts_reached": self._stats["max_attempts_reached"],
        }

    def reset_statistics(self):
        """Reset all statistics"""
        self._stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_attempts": 0,
            "max_attempts_reached": 0,
        }

    @asynccontextmanager
    async def retry(self):
        """Use retry policy as async context manager"""
        yield self

    @staticmethod
    def for_database() -> 'RetryPolicy':
        return RetryPolicy(config=RetryConfig(max_attempts=3, base_delay_ms=50, max_delay_ms=2000))

    @staticmethod
    def for_external_api() -> 'RetryPolicy':
        return RetryPolicy(config=RetryConfig(max_attempts=4, base_delay_ms=200, max_delay_ms=5000))

    @staticmethod
    def for_message_broker() -> 'RetryPolicy':
        return RetryPolicy(config=RetryConfig(max_attempts=5, base_delay_ms=100, max_delay_ms=10000))

    @staticmethod
    def aggressive() -> 'RetryPolicy':
        return RetryPolicy(config=RetryConfig(max_attempts=3, base_delay_ms=10, max_delay_ms=500, jitter_enabled=False))

    @staticmethod
    def conservative() -> 'RetryPolicy':
        return RetryPolicy(config=RetryConfig(max_attempts=3, base_delay_ms=500, max_delay_ms=30000))
