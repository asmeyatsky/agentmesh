"""
Bulkhead Isolation Pattern

Isolates resources to prevent cascading failures.

Guarantees:
- Maximum concurrent calls are bounded
- Queue size is limited to prevent memory issues
- Different operations don't starve each other
- Observability into resource utilization
"""

import asyncio
import logging
from typing import Optional, Callable, Awaitable, TypeVar, Any


T = TypeVar('T')


class BulkheadException(Exception):
    """Exception raised when bulkhead limits are exceeded"""
    pass


class BulkheadIsolation:
    """
    Bulkhead pattern for resource isolation.

    Prevents one slow/failing subsystem from exhausting
    resources needed by other subsystems.

    Properties:
    - Limits concurrent calls (semaphore)
    - Limits queue size (backpressure)
    - Tracks utilization metrics
    """

    def __init__(self,
                 name: str,
                 max_concurrent_calls: int = 100,
                 max_queue_size: int = 1000,
                 timeout_seconds: Optional[float] = None):
        """
        Initialize bulkhead isolation

        Args:
            name: Bulkhead identifier
            max_concurrent_calls: Maximum concurrent call limit
            max_queue_size: Maximum requests in queue
            timeout_seconds: Optional timeout for acquiring semaphore
        """
        self.name = name
        self.max_concurrent_calls = max_concurrent_calls
        self.max_queue_size = max_queue_size
        self.timeout_seconds = timeout_seconds

        self.semaphore = asyncio.Semaphore(max_concurrent_calls)
        self.queue_size = 0
        self.active_calls = 0
        self.total_calls = 0
        self.rejected_calls = 0

        self.logger = logging.getLogger(f"bulkhead.{name}")

    async def execute(self,
                     func: Callable[..., Awaitable[T]],
                     *args,
                     **kwargs) -> T:
        """
        Execute function within bulkhead isolation.

        Args:
            func: Async function to execute
            args: Function arguments
            kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            BulkheadException: If bulkhead limits exceeded or operation times out
        """
        # Check queue size to prevent memory exhaustion
        if self.queue_size >= self.max_queue_size:
            self.rejected_calls += 1
            raise BulkheadException(
                f"Bulkhead '{self.name}' queue is full "
                f"({self.queue_size}/{self.max_queue_size})"
            )

        self.queue_size += 1
        self.total_calls += 1

        try:
            # Acquire semaphore with optional timeout
            try:
                await asyncio.wait_for(
                    self.semaphore.acquire(),
                    timeout=self.timeout_seconds
                )
            except asyncio.TimeoutError:
                self.rejected_calls += 1
                raise BulkheadException(
                    f"Bulkhead '{self.name}' semaphore timeout "
                    f"({self.active_calls}/{self.max_concurrent_calls} active)"
                )

            self.queue_size -= 1
            self.active_calls += 1

            try:
                # Execute function
                return await func(*args, **kwargs)
            finally:
                self.active_calls -= 1
                self.semaphore.release()

        except BulkheadException:
            raise
        except Exception as e:
            self.logger.error(f"Error in bulkhead {self.name}: {str(e)}")
            raise

    def execute_sync(self,
                    func: Callable[..., T],
                    *args,
                    **kwargs) -> T:
        """
        Execute synchronous function within bulkhead isolation.

        Note: For sync code in async context, use execute() with
              asyncio.to_thread() instead.

        Args:
            func: Sync function to execute
            args: Function arguments
            kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            BulkheadException: If bulkhead limits exceeded
        """
        # Check queue size
        if self.queue_size >= self.max_queue_size:
            self.rejected_calls += 1
            raise BulkheadException(
                f"Bulkhead '{self.name}' queue is full "
                f"({self.queue_size}/{self.max_queue_size})"
            )

        self.queue_size += 1
        self.total_calls += 1

        try:
            # Check if we can acquire immediately (non-async)
            if not self.semaphore._value > 0:
                self.rejected_calls += 1
                raise BulkheadException(
                    f"Bulkhead '{self.name}' at capacity "
                    f"({self.active_calls}/{self.max_concurrent_calls} active)"
                )

            self.semaphore._value -= 1
            self.queue_size -= 1
            self.active_calls += 1

            try:
                return func(*args, **kwargs)
            finally:
                self.active_calls -= 1
                self.semaphore._value += 1

        except BulkheadException:
            raise
        except Exception as e:
            self.logger.error(f"Error in bulkhead {self.name}: {str(e)}")
            raise

    def get_metrics(self) -> dict:
        """Get bulkhead utilization metrics"""
        utilization_percent = (self.active_calls / self.max_concurrent_calls) * 100

        return {
            "name": self.name,
            "max_concurrent_calls": self.max_concurrent_calls,
            "active_calls": self.active_calls,
            "queue_size": self.queue_size,
            "max_queue_size": self.max_queue_size,
            "utilization_percent": utilization_percent,
            "total_calls": self.total_calls,
            "rejected_calls": self.rejected_calls,
            "rejection_rate_percent": (
                (self.rejected_calls / self.total_calls * 100)
                if self.total_calls > 0 else 0
            )
        }

    def is_healthy(self) -> bool:
        """Check bulkhead health"""
        utilization = (self.active_calls / self.max_concurrent_calls)
        rejection_rate = (
            self.rejected_calls / self.total_calls
            if self.total_calls > 0 else 0
        )

        # Unhealthy if usage very high or rejection rate significant
        return utilization < 0.95 and rejection_rate < 0.05


class BulkheadManager:
    """
    Manages multiple bulkhead instances.

    Provides:
    - Centralized bulkhead management
    - Metrics aggregation
    - Health checks
    """

    def __init__(self):
        """Initialize bulkhead manager"""
        self.bulkheads: dict[str, BulkheadIsolation] = {}

    def register(self,
                 name: str,
                 bulkhead: BulkheadIsolation) -> BulkheadIsolation:
        """Register bulkhead"""
        self.bulkheads[name] = bulkhead
        return bulkhead

    def get(self, name: str) -> Optional[BulkheadIsolation]:
        """Get bulkhead by name"""
        return self.bulkheads.get(name)

    def get_all_metrics(self) -> dict:
        """Get metrics for all bulkheads"""
        return {
            name: bulkhead.get_metrics()
            for name, bulkhead in self.bulkheads.items()
        }

    def get_health(self) -> dict:
        """Get health status of all bulkheads"""
        return {
            name: bulkhead.is_healthy()
            for name, bulkhead in self.bulkheads.items()
        }

    @staticmethod
    def for_database(max_concurrent: int = 20) -> BulkheadIsolation:
        """Create bulkhead optimized for database connections"""
        return BulkheadIsolation(
            name="database",
            max_concurrent_calls=max_concurrent,
            max_queue_size=1000
        )

    @staticmethod
    def for_external_api(max_concurrent: int = 50) -> BulkheadIsolation:
        """Create bulkhead optimized for external API calls"""
        return BulkheadIsolation(
            name="external_api",
            max_concurrent_calls=max_concurrent,
            max_queue_size=500,
            timeout_seconds=30.0
        )

    @staticmethod
    def for_message_broker(max_concurrent: int = 100) -> BulkheadIsolation:
        """Create bulkhead optimized for message broker"""
        return BulkheadIsolation(
            name="message_broker",
            max_concurrent_calls=max_concurrent,
            max_queue_size=2000
        )
