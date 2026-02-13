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
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Callable, Awaitable, TypeVar, Any

T = TypeVar('T')


class BulkheadException(Exception):
    """Base exception for bulkhead errors"""
    pass


class BulkheadFullError(BulkheadException):
    """Exception raised when bulkhead queue is full"""
    pass


class BulkheadTimeoutError(BulkheadException):
    """Exception raised when a task times out"""
    pass


@dataclass
class BulkheadConfig:
    """Configuration for Bulkhead"""
    max_concurrent: int = 10
    max_queue: int = 50
    timeout_ms: int = 30000
    enable_metrics: bool = True
    queue_timeout_ms: int = 5000


@dataclass
class BulkheadTask:
    """Represents a task submitted to the bulkhead"""
    id: str
    func: Callable
    args: tuple
    kwargs: dict
    created_at: datetime
    result: Any = None
    error: Optional[Exception] = None
    completed_at: Optional[datetime] = None
    execution_duration_ms: Optional[float] = None

    def complete(self, result: Any, completed_at: datetime, error: Optional[Exception] = None):
        """Mark task as completed"""
        self.result = result
        self.error = error
        self.completed_at = completed_at
        delta = (completed_at - self.created_at)
        self.execution_duration_ms = delta.total_seconds() * 1000


@dataclass
class BulkheadStats:
    """Statistics for bulkhead usage"""
    total_submitted: int = 0
    total_completed: int = 0
    total_failed: int = 0
    total_timed_out: int = 0
    total_rejected: int = 0
    current_executing: int = 0
    current_queued: int = 0
    average_execution_time_ms: float = 0.0
    max_execution_time_ms: float = 0
    min_execution_time_ms: float = float("inf")
    _execution_times: list = field(default_factory=list)

    def record_execution(self, duration_ms: float, success: bool = True):
        """Record an execution result"""
        self._execution_times.append(duration_ms)
        if success:
            self.total_completed += 1
        else:
            self.total_failed += 1
        self.max_execution_time_ms = max(self.max_execution_time_ms, duration_ms)
        self.min_execution_time_ms = min(self.min_execution_time_ms, duration_ms)
        self.average_execution_time_ms = sum(self._execution_times) / len(self._execution_times)

    def record_rejection(self):
        self.total_rejected += 1

    def record_timeout(self):
        self.total_timed_out += 1


class Bulkhead:
    """
    Bulkhead pattern for resource isolation.

    Prevents one slow/failing subsystem from exhausting
    resources needed by other subsystems.
    """

    def __init__(self,
                 config: Optional[BulkheadConfig] = None,
                 name: str = "default",
                 max_concurrent: Optional[int] = None,
                 max_queue: Optional[int] = None,
                 timeout: Optional[float] = None):
        if config is None:
            config = BulkheadConfig()
        if max_concurrent is not None:
            config.max_concurrent = max_concurrent
        if max_queue is not None:
            config.max_queue = max_queue
        if timeout is not None:
            config.timeout_ms = int(timeout * 1000)

        self.config = config
        self.name = name
        self._semaphore = asyncio.Semaphore(config.max_concurrent)
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=config.max_queue)
        self._stats = BulkheadStats()
        self._shutdown = False
        self.logger = logging.getLogger(f"bulkhead.{name}")

    async def execute(self,
                      func: Callable,
                      *args,
                      **kwargs) -> Any:
        """Execute function within bulkhead isolation."""
        import inspect

        if self._shutdown:
            raise BulkheadFullError("Bulkhead is shut down")

        self._stats.total_submitted += 1

        # Check queue capacity: reject if all concurrent slots are busy
        # AND the queue is full
        if self._semaphore._value == 0 and self._stats.current_queued >= self.config.max_queue:
            self._stats.record_rejection()
            raise BulkheadFullError(
                f"Bulkhead queue is full ({self._stats.current_queued}/{self.config.max_queue})"
            )

        self._stats.current_queued += 1

        try:
            # Wait for semaphore (no separate queue timeout — use main timeout)
            await self._semaphore.acquire()

            self._stats.current_queued -= 1
            self._stats.current_executing += 1

            start = datetime.now()
            try:
                if inspect.iscoroutinefunction(func):
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=self.config.timeout_ms / 1000
                    )
                else:
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(None, lambda: func(*args, **kwargs)),
                        timeout=self.config.timeout_ms / 1000
                    )

                end = datetime.now()
                duration_ms = (end - start).total_seconds() * 1000
                self._stats.record_execution(duration_ms, success=True)
                return result

            except asyncio.TimeoutError:
                self._stats.record_timeout()
                raise BulkheadTimeoutError(
                    f"Task timed out after {self.config.timeout_ms}ms"
                )
            except BulkheadTimeoutError:
                raise
            except Exception as e:
                end = datetime.now()
                duration_ms = (end - start).total_seconds() * 1000
                self._stats.record_execution(duration_ms, success=False)
                raise

            finally:
                self._stats.current_executing -= 1
                self._semaphore.release()

        except (BulkheadFullError, BulkheadTimeoutError):
            raise
        except Exception:
            raise

    async def shutdown(self, timeout_ms: int = 5000):
        """Gracefully shut down the bulkhead"""
        self._shutdown = True
        # Wait for executing tasks to complete
        try:
            await asyncio.wait_for(
                self._wait_for_completion(),
                timeout=timeout_ms / 1000
            )
        except asyncio.TimeoutError:
            self.logger.warning(f"Bulkhead '{self.name}' shutdown timed out")

    async def _wait_for_completion(self):
        """Wait for all executing tasks to complete"""
        while self._stats.current_executing > 0:
            await asyncio.sleep(0.01)

    def get_stats(self) -> BulkheadStats:
        """Get bulkhead statistics"""
        return self._stats

    def reset_statistics(self):
        """Reset statistics"""
        self._stats = BulkheadStats()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()
        return False


# Backward-compatible alias
BulkheadIsolation = Bulkhead


class BulkheadManager:
    """Manages multiple bulkhead instances."""

    def __init__(self):
        self.bulkheads: dict[str, Bulkhead] = {}

    def register(self, name: str, bulkhead: Bulkhead) -> Bulkhead:
        self.bulkheads[name] = bulkhead
        return bulkhead

    def get(self, name: str) -> Optional[Bulkhead]:
        return self.bulkheads.get(name)

    def get_all_metrics(self) -> dict:
        return {
            name: {
                "total_submitted": b.get_stats().total_submitted,
                "total_completed": b.get_stats().total_completed,
                "current_executing": b.get_stats().current_executing,
            }
            for name, b in self.bulkheads.items()
        }

    def get_health(self) -> dict:
        return {name: True for name in self.bulkheads}

    @staticmethod
    def for_database(max_concurrent: int = 20) -> Bulkhead:
        return Bulkhead(config=BulkheadConfig(max_concurrent=max_concurrent, max_queue=1000), name="database")

    @staticmethod
    def for_external_api(max_concurrent: int = 50) -> Bulkhead:
        return Bulkhead(config=BulkheadConfig(max_concurrent=max_concurrent, max_queue=500, timeout_ms=30000), name="external_api")

    @staticmethod
    def for_message_broker(max_concurrent: int = 100) -> Bulkhead:
        return Bulkhead(config=BulkheadConfig(max_concurrent=max_concurrent, max_queue=2000), name="message_broker")
