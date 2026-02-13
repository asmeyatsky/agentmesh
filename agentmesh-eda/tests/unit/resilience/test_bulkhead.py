"""
Bulkhead Module Tests

Tests for the bulkhead pattern implementation including
concurrency limits, queue management, and resource isolation.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List
import time

from agentmesh.infrastructure.resilience.bulkhead import (
    Bulkhead,
    BulkheadConfig,
    BulkheadStats,
    BulkheadFullError,
    BulkheadTimeoutError,
    BulkheadTask,
)


class TestBulkheadConfig:
    """Test BulkheadConfig model"""

    def test_default_config(self):
        """Test default bulkhead configuration"""
        config = BulkheadConfig()

        assert config.max_concurrent == 10
        assert config.max_queue == 50
        assert config.timeout_ms == 30000
        assert config.enable_metrics is True
        assert config.queue_timeout_ms == 5000

    def test_custom_config(self):
        """Test custom bulkhead configuration"""
        config = BulkheadConfig(
            max_concurrent=5,
            max_queue=20,
            timeout_ms=10000,
            enable_metrics=False,
            queue_timeout_ms=2000,
        )

        assert config.max_concurrent == 5
        assert config.max_queue == 20
        assert config.timeout_ms == 10000
        assert config.enable_metrics is False
        assert config.queue_timeout_ms == 2000


class TestBulkheadTask:
    """Test BulkheadTask model"""

    def test_task_creation(self):
        """Test creating a bulkhead task"""

        async def task_func():
            return "result"

        task = BulkheadTask(
            id="task123", func=task_func, args=(), kwargs={}, created_at=datetime.now()
        )

        assert task.id == "task123"
        assert task.func == task_func
        assert task.args == ()
        assert task.kwargs == {}
        assert task.result is None
        assert task.error is None
        assert task.completed_at is None
        assert task.execution_duration_ms is None

    def test_task_completion(self):
        """Test marking a task as completed"""

        async def task_func():
            return "success"

        task = BulkheadTask(
            id="task123", func=task_func, args=(), kwargs={}, created_at=datetime.now()
        )

        completed_at = datetime.now()
        task.complete("success", completed_at)

        assert task.result == "success"
        assert task.error is None
        assert task.completed_at == completed_at
        assert task.execution_duration_ms is not None

    def test_task_failure(self):
        """Test marking a task as failed"""
        error = ValueError("task failed")

        async def task_func():
            raise error

        task = BulkheadTask(
            id="task123", func=task_func, args=(), kwargs={}, created_at=datetime.now()
        )

        completed_at = datetime.now()
        task.complete(None, completed_at, error)

        assert task.result is None
        assert task.error == error
        assert task.completed_at == completed_at

    def test_task_execution_time_calculation(self):
        """Test task execution time calculation"""
        created_at = datetime.now()

        async def task_func():
            return "result"

        task = BulkheadTask(
            id="task123", func=task_func, args=(), kwargs={}, created_at=created_at
        )

        # Simulate execution time
        completed_at = created_at + timedelta(milliseconds=250)
        task.complete("result", completed_at)

        assert task.execution_duration_ms == 250


class TestBulkheadStats:
    """Test BulkheadStats model"""

    def test_stats_initialization(self):
        """Test statistics initialization"""
        stats = BulkheadStats()

        assert stats.total_submitted == 0
        assert stats.total_completed == 0
        assert stats.total_failed == 0
        assert stats.total_timed_out == 0
        assert stats.total_rejected == 0
        assert stats.current_executing == 0
        assert stats.current_queued == 0
        assert stats.average_execution_time_ms == 0.0
        assert stats.max_execution_time_ms == 0
        assert stats.min_execution_time_ms == float("inf")

    def test_stats_update_execution(self):
        """Test updating statistics with execution data"""
        stats = BulkheadStats()

        # Record some executions
        stats.record_execution(100.0, success=True)
        stats.record_execution(200.0, success=True)
        stats.record_execution(50.0, success=False)

        assert stats.total_completed == 2
        assert stats.total_failed == 1
        assert (
            stats.average_execution_time_ms == 116.66666666666667
        )  # (100 + 200 + 50) / 3
        assert stats.max_execution_time_ms == 200.0
        assert stats.min_execution_time_ms == 50.0

    def test_stats_update_rejection(self):
        """Test updating statistics with rejection data"""
        stats = BulkheadStats()

        stats.record_rejection()
        stats.record_timeout()

        assert stats.total_rejected == 1
        assert stats.total_timed_out == 1


class TestBulkhead:
    """Test Bulkhead functionality"""

    @pytest.fixture
    def bulkhead(self):
        """Create a bulkhead with default config"""
        return Bulkhead()

    @pytest.fixture
    def custom_config(self):
        """Create custom bulkhead configuration"""
        return BulkheadConfig(
            max_concurrent=2, max_queue=3, timeout_ms=1000, queue_timeout_ms=500
        )

    @pytest.fixture
    def small_bulkhead(self, custom_config):
        """Create a small bulkhead for testing limits"""
        return Bulkhead(config=custom_config)

    def test_bulkhead_initialization(self):
        """Test bulkhead initialization"""
        config = BulkheadConfig(max_concurrent=5, max_queue=10)
        bulkhead = Bulkhead(config=config, name="test_bulkhead")

        assert bulkhead.config == config
        assert bulkhead.name == "test_bulkhead"
        assert bulkhead._semaphore._value == 5
        assert bulkhead._queue.maxsize == 10

    @pytest.mark.asyncio
    async def test_execute_successful_task(self, bulkhead):
        """Test executing a successful task"""

        async def task_func():
            await asyncio.sleep(0.1)
            return "success"

        result = await bulkhead.execute(task_func)

        assert result == "success"

        stats = bulkhead.get_stats()
        assert stats.total_submitted == 1
        assert stats.total_completed == 1
        assert stats.total_failed == 0

    @pytest.mark.asyncio
    async def test_execute_failing_task(self, bulkhead):
        """Test executing a task that fails"""
        error = ValueError("task failed")

        async def failing_func():
            raise error

        with pytest.raises(ValueError, match="task failed"):
            await bulkhead.execute(failing_func)

        stats = bulkhead.get_stats()
        assert stats.total_submitted == 1
        assert stats.total_completed == 0
        assert stats.total_failed == 1

    @pytest.mark.asyncio
    async def test_concurrent_execution_limit(self, small_bulkhead):
        """Test concurrent execution limit"""
        executing_count = 0
        max_executing = 0

        async def long_task():
            nonlocal executing_count, max_executing
            executing_count += 1
            max_executing = max(max_executing, executing_count)
            await asyncio.sleep(0.2)
            executing_count -= 1
            return "completed"

        # Submit more tasks than concurrent limit
        tasks = [
            small_bulkhead.execute(long_task)
            for _ in range(5)  # 5 tasks, max_concurrent=2
        ]

        await asyncio.gather(*tasks)

        assert max_executing == 2  # Should not exceed concurrent limit
        assert executing_count == 0  # All tasks completed

        stats = small_bulkhead.get_stats()
        assert stats.total_completed == 5

    @pytest.mark.asyncio
    async def test_queue_limit(self, small_bulkhead):
        """Test queue size limit"""

        async def blocking_task():
            await asyncio.sleep(0.3)
            return "completed"

        # Start tasks that will occupy all concurrent slots
        blocking_tasks = [
            asyncio.create_task(small_bulkhead.execute(blocking_task))
            for _ in range(2)  # max_concurrent=2
        ]

        # Give them time to start
        await asyncio.sleep(0.01)

        # Fill the queue
        queue_tasks = []
        for i in range(3):  # max_queue=3
            task = asyncio.create_task(small_bulkhead.execute(blocking_task))
            queue_tasks.append(task)
            await asyncio.sleep(0.01)

        # Next task should be rejected
        with pytest.raises(BulkheadFullError, match="Bulkhead queue is full"):
            await small_bulkhead.execute(blocking_task)

        # Complete all tasks
        await asyncio.gather(*blocking_tasks, *queue_tasks)

        stats = small_bulkhead.get_stats()
        assert stats.total_rejected == 1
        assert stats.total_completed == 5

    @pytest.mark.asyncio
    async def test_timeout_handling(self, small_bulkhead):
        """Test task timeout handling"""

        async def slow_task():
            await asyncio.sleep(2)  # Longer than timeout_ms=1000
            return "should_not_complete"

        with pytest.raises(BulkheadTimeoutError, match="Task timed out"):
            await small_bulkhead.execute(slow_task)

        stats = small_bulkhead.get_stats()
        assert stats.total_timed_out == 1

    @pytest.mark.asyncio
    async def test_execute_with_arguments(self, bulkhead):
        """Test executing task with arguments"""

        async def task_with_args(x: int, y: str, flag: bool = False):
            return f"{x}-{y}-{flag}"

        result = await bulkhead.execute(task_with_args, 42, "test", flag=True)

        assert result == "42-test-True"

        stats = bulkhead.get_stats()
        assert stats.total_completed == 1

    @pytest.mark.asyncio
    async def test_execute_sync_function(self, bulkhead):
        """Test executing a synchronous function"""

        def sync_func(x: int) -> int:
            return x * 2

        result = await bulkhead.execute(sync_func, 21)

        assert result == 42

        stats = bulkhead.get_stats()
        assert stats.total_completed == 1

    @pytest.mark.asyncio
    async def test_context_manager_usage(self, small_bulkhead):
        """Test using bulkhead as context manager"""
        async with small_bulkhead:

            async def task_func():
                return "context_success"

            result = await small_bulkhead.execute(task_func)
            assert result == "context_success"

        # Bulkhead should be properly shut down
        assert small_bulkhead._shutdown is True

    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, bulkhead):
        """Test graceful shutdown of bulkhead"""
        executing_tasks = []
        completed_tasks = []

        async def task_func(task_id: int):
            executing_tasks.append(task_id)
            await asyncio.sleep(0.1)
            executing_tasks.remove(task_id)
            completed_tasks.append(task_id)
            return task_id

        # Start some tasks
        tasks = [asyncio.create_task(bulkhead.execute(task_func, i)) for i in range(5)]

        # Wait a bit then shutdown
        await asyncio.sleep(0.05)
        await bulkhead.shutdown()

        # All tasks should complete despite shutdown
        results = await asyncio.gather(*tasks, return_exceptions=True)

        assert len(completed_tasks) == 5
        assert all(isinstance(r, int) for r in results if not isinstance(r, Exception))

    @pytest.mark.asyncio
    async def test_shutdown_timeout(self, small_bulkhead):
        """Test shutdown timeout handling"""

        async def very_long_task():
            await asyncio.sleep(10)  # Longer than shutdown timeout
            return "should_not_complete"

        # Start a long task
        task = asyncio.create_task(small_bulkhead.execute(very_long_task))
        await asyncio.sleep(0.01)

        # Shutdown with short timeout
        await small_bulkhead.shutdown(timeout_ms=100)

        # Bulkhead should be marked as shut down
        assert small_bulkhead._shutdown is True

        # Cancel the lingering task to clean up
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, BulkheadTimeoutError):
            pass

    def test_get_statistics(self, bulkhead):
        """Test getting bulkhead statistics"""
        stats = bulkhead.get_stats()

        assert isinstance(stats, BulkheadStats)
        assert stats.total_submitted >= 0
        assert stats.current_executing >= 0
        assert stats.current_queued >= 0

    def test_reset_statistics(self, bulkhead):
        """Test resetting bulkhead statistics"""
        # Manually update some stats
        bulkhead._stats.total_submitted = 10
        bulkhead._stats.total_completed = 8

        bulkhead.reset_statistics()

        stats = bulkhead.get_stats()
        assert stats.total_submitted == 0
        assert stats.total_completed == 0

    @pytest.mark.asyncio
    async def test_metrics_collection(self, bulkhead):
        """Test metrics collection when enabled"""
        if not bulkhead.config.enable_metrics:
            pytest.skip("Metrics not enabled")

        # Execute some tasks to generate metrics
        for i in range(3):
            await bulkhead.execute(lambda i=i: f"task_{i}")

        # Try to execute a failing task
        try:
            await bulkhead.execute(lambda: 1 / 0)
        except:
            pass

        stats = bulkhead.get_stats()
        assert stats.total_submitted == 4
        assert stats.total_completed == 3
        assert stats.total_failed == 1
        assert stats.average_execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, bulkhead):
        """Test integration with circuit breaker"""
        from agentmesh.infrastructure.resilience.circuit_breaker import (
            CircuitBreaker,
            CircuitState,
        )

        circuit_breaker = CircuitBreaker(failure_threshold=1)
        call_count = 0

        async def protected_task():
            nonlocal call_count
            call_count += 1
            if circuit_breaker.state == CircuitState.OPEN:
                raise ConnectionError("Circuit is open")
            if call_count >= 2:
                circuit_breaker.record_failure()
                raise ValueError("Task failed")
            return "success"

        # First call should succeed
        result = await bulkhead.execute(protected_task)
        assert result == "success"

        # Second call should fail but circuit still closed
        with pytest.raises(ValueError):
            await bulkhead.execute(protected_task)

        # Third call should fail due to open circuit
        with pytest.raises(ConnectionError):
            await bulkhead.execute(protected_task)

    @pytest.mark.asyncio
    async def test_retry_policy_integration(self, bulkhead):
        """Test integration with retry policy"""
        from agentmesh.infrastructure.resilience.retry_policy import (
            RetryPolicy,
            RetryConfig,
        )

        retry_config = RetryConfig(max_attempts=2, base_delay_ms=10)
        retry_policy = RetryPolicy(config=retry_config)

        call_count = 0

        async def flaky_task():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("temporary failure")
            return "retry_success"

        async def retried_task():
            result = await retry_policy.execute(flaky_task)
            return result.result

        result = await bulkhead.execute(retried_task)

        assert result == "retry_success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_performance_benchmarks(self):
        """Test bulkhead performance characteristics"""
        # Use a bulkhead with enough queue space for 100 tasks
        perf_bulkhead = Bulkhead(config=BulkheadConfig(
            max_concurrent=10, max_queue=100, timeout_ms=10000
        ))
        num_tasks = 100
        task_duration_ms = 10

        async def quick_task(task_id: int):
            await asyncio.sleep(task_duration_ms / 1000)
            return task_id

        start_time = time.time()

        # Execute many tasks concurrently
        tasks = [
            asyncio.create_task(perf_bulkhead.execute(quick_task, i))
            for i in range(num_tasks)
        ]

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        total_time_ms = (end_time - start_time) * 1000

        assert len(results) == num_tasks
        assert sorted(results) == list(range(num_tasks))

        # Performance should be reasonable
        assert total_time_ms < 1000  # Allow generous overhead

        stats = perf_bulkhead.get_stats()
        assert stats.total_completed == num_tasks
        assert stats.average_execution_time_ms > 0
