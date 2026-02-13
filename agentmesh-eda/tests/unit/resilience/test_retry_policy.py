"""
Retry Policy Module Tests

Tests for the retry policy functionality including
exponential backoff, jitter, max attempts, and failure handling.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, Callable, Type

from agentmesh.infrastructure.resilience.retry_policy import (
    RetryPolicy,
    RetryConfig,
    RetryResult,
    RetryState,
    RetryableError,
    NonRetryableError,
    MaxRetriesExceededError,
)


class TestRetryConfig:
    """Test RetryConfig model"""

    def test_default_config(self):
        """Test default retry configuration"""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.base_delay_ms == 100
        assert config.max_delay_ms == 30000
        assert config.backoff_multiplier == 2.0
        assert config.jitter_enabled is True
        assert config.jitter_range_ms == 100

    def test_custom_config(self):
        """Test custom retry configuration"""
        config = RetryConfig(
            max_attempts=5,
            base_delay_ms=50,
            max_delay_ms=10000,
            backoff_multiplier=1.5,
            jitter_enabled=False,
            jitter_range_ms=50,
        )

        assert config.max_attempts == 5
        assert config.base_delay_ms == 50
        assert config.max_delay_ms == 10000
        assert config.backoff_multiplier == 1.5
        assert config.jitter_enabled is False
        assert config.jitter_range_ms == 50

    def test_calculate_delay_with_backoff(self):
        """Test delay calculation with exponential backoff"""
        config = RetryConfig(
            base_delay_ms=100, backoff_multiplier=2.0, jitter_enabled=False
        )

        # First retry: 100ms
        delay = config.calculate_delay(attempt=1)
        assert delay == 100

        # Second retry: 200ms (100 * 2^1)
        delay = config.calculate_delay(attempt=2)
        assert delay == 200

        # Third retry: 400ms (100 * 2^2)
        delay = config.calculate_delay(attempt=3)
        assert delay == 400

    def test_calculate_delay_with_max_cap(self):
        """Test delay calculation with maximum delay cap"""
        config = RetryConfig(
            base_delay_ms=100,
            backoff_multiplier=3.0,
            max_delay_ms=500,
            jitter_enabled=False,
        )

        # Should be capped at max_delay_ms
        delay = config.calculate_delay(attempt=5)  # Would be 100 * 3^4 = 8100
        assert delay == 500

    def test_calculate_delay_with_jitter(self):
        """Test delay calculation with jitter"""
        config = RetryConfig(base_delay_ms=100, jitter_enabled=True, jitter_range_ms=50)

        delay = config.calculate_delay(attempt=1)

        # Should be base_delay +/- jitter_range
        assert 50 <= delay <= 150

    def test_is_retryable_exception(self):
        """Test exception retryability determination"""
        config = RetryConfig()

        # Default retryable exceptions
        assert config.is_retryable_exception(ConnectionError("timeout"))
        assert config.is_retryable_exception(TimeoutError("timeout"))
        assert config.is_retryable_exception(RetryableError("retry me"))

        # Default non-retryable exceptions
        assert not config.is_retryable_exception(ValueError("invalid input"))
        assert not config.is_retryable_exception(NonRetryableError("don't retry"))
        assert not config.is_retryable_exception(KeyError("not found"))

    def test_custom_retryable_exceptions(self):
        """Test custom retryable exceptions configuration"""
        config = RetryConfig(
            retryable_exceptions=[ValueError, TypeError],
            non_retryable_exceptions=[ConnectionError],
        )

        assert config.is_retryable_exception(ValueError("invalid"))
        assert config.is_retryable_exception(TypeError("wrong type"))
        assert not config.is_retryable_exception(ConnectionError("connection failed"))


class TestRetryResult:
    """Test RetryResult model"""

    def test_successful_result(self):
        """Test successful retry result"""
        result = RetryResult(
            success=True, result="success_value", attempts=2, total_duration_ms=250
        )

        assert result.success is True
        assert result.result == "success_value"
        assert result.attempts == 2
        assert result.total_duration_ms == 250
        assert result.error is None

    def test_failed_result(self):
        """Test failed retry result"""
        error = ValueError("final error")
        result = RetryResult(
            success=False, error=error, attempts=3, total_duration_ms=550
        )

        assert result.success is False
        assert result.error == error
        assert result.attempts == 3
        assert result.total_duration_ms == 550
        assert result.result is None


class TestRetryState:
    """Test RetryState model"""

    def test_retry_state_initialization(self):
        """Test retry state initialization"""
        error = ConnectionError("timeout")
        state = RetryState(
            attempt=1, last_error=error, total_delay_ms=100
        )

        assert state.attempt == 1
        assert state.last_error is error
        assert isinstance(state.last_error, ConnectionError)
        assert str(state.last_error) == "timeout"
        assert state.total_delay_ms == 100
        assert state.start_time is not None

    def test_should_continue_retrying(self):
        """Test retry continuation logic"""
        config = RetryConfig(max_attempts=3)

        # Should continue on first attempt with retryable error
        state = RetryState(
            attempt=1, last_error=ConnectionError("timeout"), total_delay_ms=100
        )
        assert state.should_continue_retrying(config) is True

        # Should not continue on max attempts
        state.attempt = 3
        assert state.should_continue_retrying(config) is False

        # Should not continue on non-retryable error
        state.attempt = 1
        state.last_error = ValueError("invalid input")
        assert state.should_continue_retrying(config) is False


class TestRetryPolicy:
    """Test RetryPolicy functionality"""

    @pytest.fixture
    def retry_policy(self):
        """Create a retry policy with default config"""
        return RetryPolicy()

    @pytest.fixture
    def custom_config(self):
        """Create a custom retry configuration"""
        return RetryConfig(max_attempts=2, base_delay_ms=10, jitter_enabled=False)

    def test_retry_policy_initialization(self):
        """Test retry policy initialization"""
        config = RetryConfig(max_attempts=5)
        policy = RetryPolicy(config=config)

        assert policy.config == config

    @pytest.mark.asyncio
    async def test_execute_success_on_first_attempt(self, retry_policy):
        """Test successful execution on first attempt"""

        async def success_func():
            return "success"

        result = await retry_policy.execute(success_func)

        assert result.success is True
        assert result.result == "success"
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_execute_success_after_retry(self, retry_policy):
        """Test successful execution after retry"""
        call_count = 0

        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("timeout")
            return "success"

        result = await retry_policy.execute(flaky_func)

        assert result.success is True
        assert result.result == "success"
        assert result.attempts == 2

    @pytest.mark.asyncio
    async def test_execute_max_retries_exceeded(self, custom_config):
        """Test execution when max retries exceeded"""
        policy = RetryPolicy(config=custom_config)

        async def failing_func():
            raise ConnectionError("always fails")

        result = await policy.execute(failing_func)

        assert result.success is False
        assert isinstance(result.error, MaxRetriesExceededError)
        assert result.attempts == custom_config.max_attempts

    @pytest.mark.asyncio
    async def test_execute_non_retryable_error(self, retry_policy):
        """Test execution with non-retryable error"""

        async def failing_func():
            raise ValueError("invalid input")

        result = await retry_policy.execute(failing_func)

        assert result.success is False
        assert isinstance(result.error, ValueError)
        assert str(result.error) == "invalid input"
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_execute_with_custom_retryable_exceptions(self, custom_config):
        """Test execution with custom retryable exceptions"""
        config = RetryConfig(
            max_attempts=2, retryable_exceptions=[ValueError], jitter_enabled=False
        )
        policy = RetryPolicy(config=config)

        call_count = 0

        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("retry me")
            return "success"

        result = await policy.execute(flaky_func)

        assert result.success is True
        assert result.attempts == 2

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self, retry_policy):
        """Test execution with timeout"""

        async def slow_func():
            await asyncio.sleep(2)
            return "slow_success"

        result = await retry_policy.execute(slow_func, timeout_ms=500)

        assert result.success is False
        assert "timeout" in str(result.error).lower()

    @pytest.mark.asyncio
    async def test_execute_with_progress_callback(self, retry_policy):
        """Test execution with progress callback"""
        progress_calls = []

        def progress_callback(state: RetryState):
            progress_calls.append(state.attempt)

        async def flaky_func():
            if len(progress_calls) == 0:
                raise ConnectionError("timeout")
            return "success"

        result = await retry_policy.execute(
            flaky_func, progress_callback=progress_callback
        )

        assert result.success is True
        assert progress_calls == [1, 2]

    @pytest.mark.asyncio
    async def test_execute_sync_function(self, retry_policy):
        """Test executing a synchronous function"""

        def sync_func():
            return "sync_result"

        result = await retry_policy.execute(sync_func)

        assert result.success is True
        assert result.result == "sync_result"

    @pytest.mark.asyncio
    async def test_context_manager_usage(self, custom_config):
        """Test using retry policy as context manager"""
        policy = RetryPolicy(config=custom_config)
        call_count = 0

        async with policy.retry() as retryer:

            async def flaky_func():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise ConnectionError("timeout")
                return "context_success"

            result = await retryer.execute(flaky_func)

        assert result.success is True
        assert result.attempts == 2

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, retry_policy):
        """Test integration with circuit breaker"""
        from agentmesh.infrastructure.resilience.circuit_breaker import (
            CircuitBreaker,
            CircuitState,
        )

        circuit_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_ms=1000)

        async def failing_func():
            circuit_breaker.record_failure()
            if circuit_breaker.state == CircuitState.OPEN:
                raise ConnectionError("circuit open")
            raise ValueError("function error")

        result = await retry_policy.execute(failing_func)

        assert result.success is False

    @pytest.mark.asyncio
    async def test_bulkhead_integration(self, retry_policy):
        """Test integration with bulkhead"""
        from agentmesh.infrastructure.resilience.bulkhead import Bulkhead

        bulkhead = Bulkhead(max_concurrent=2, max_queue=2)

        async def delayed_func(delay_ms: int):
            await asyncio.sleep(delay_ms / 1000)
            return f"delayed_{delay_ms}"

        # Execute multiple tasks through bulkhead
        tasks = [
            retry_policy.execute(
                lambda d=delay: bulkhead.execute(lambda: delayed_func(d))
            )
            for delay in [100, 200, 50]
        ]

        results = await asyncio.gather(*tasks)

        assert all(r.success for r in results)

    def test_retry_statistics(self, retry_policy):
        """Test retry statistics tracking"""
        stats = retry_policy.get_statistics()

        assert stats["total_executions"] == 0
        assert stats["successful_executions"] == 0
        assert stats["failed_executions"] == 0
        assert stats["average_attempts"] == 0.0
        assert stats["max_attempts_reached"] == 0

    @pytest.mark.asyncio
    async def test_retry_statistics_tracking(self, retry_policy):
        """Test that statistics are properly tracked"""
        # Execute some operations
        await retry_policy.execute(lambda: "success1")
        await retry_policy.execute(lambda: "success2")

        call_count = 0

        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("retry me")
            return "success_after_retry"

        await retry_policy.execute(flaky_func)

        async def failing_func():
            raise ConnectionError("always fails")

        await retry_policy.execute(failing_func)

        stats = retry_policy.get_statistics()

        assert stats["total_executions"] == 4
        assert stats["successful_executions"] == 3
        assert stats["failed_executions"] == 1
        assert stats["average_attempts"] > 1.0
        assert stats["max_attempts_reached"] == 1

    def test_reset_statistics(self, retry_policy):
        """Test resetting statistics"""
        # Add some dummy statistics through internal method
        retry_policy._stats["total_executions"] = 10
        retry_policy._stats["successful_executions"] = 8

        retry_policy.reset_statistics()

        stats = retry_policy.get_statistics()
        assert stats["total_executions"] == 0
        assert stats["successful_executions"] == 0


class TestCustomExceptions:
    """Test custom exception classes"""

    def test_retryable_error(self):
        """Test RetryableError exception"""
        error = RetryableError("retry me")
        assert str(error) == "retry me"
        assert isinstance(error, Exception)

    def test_non_retryable_error(self):
        """Test NonRetryableError exception"""
        error = NonRetryableError("don't retry")
        assert str(error) == "don't retry"
        assert isinstance(error, Exception)

    def test_max_retries_exceeded_error(self):
        """Test MaxRetriesExceededError exception"""
        original_error = ConnectionError("timeout")
        error = MaxRetriesExceededError(
            max_attempts=3, last_error=original_error, total_duration_ms=500
        )

        assert "max attempts (3) exceeded" in str(error)
        assert error.max_attempts == 3
        assert error.last_error == original_error
        assert error.total_duration_ms == 500
