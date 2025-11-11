"""
Unit tests for Circuit Breaker pattern.

Tests:
- State transitions (CLOSED -> OPEN -> HALF_OPEN -> CLOSED)
- Failure threshold triggering
- Recovery timeout handling
- Exception handling
"""

import pytest
import asyncio
from agentmesh.infrastructure.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenException
)


class TestCircuitBreakerStates:
    """Test circuit breaker state transitions"""

    def test_initial_state_is_closed(self):
        """Circuit breaker should start in CLOSED state"""
        breaker = CircuitBreaker("test")
        assert breaker.state == CircuitState.CLOSED

    def test_transitions_to_open_after_failures(self):
        """Circuit should open after failure threshold exceeded"""
        breaker = CircuitBreaker(
            "test",
            failure_threshold=3,
            recovery_timeout_seconds=60
        )

        async def failing_func():
            raise ValueError("Test error")

        # Cause failures
        for i in range(3):
            with pytest.raises(ValueError):
                asyncio.run(breaker.call(failing_func))

        assert breaker.state == CircuitState.OPEN

    def test_rejects_calls_when_open(self):
        """Circuit should reject calls when OPEN"""
        breaker = CircuitBreaker("test", failure_threshold=1)

        async def failing_func():
            raise ValueError("Test error")

        # Cause one failure to open circuit
        with pytest.raises(ValueError):
            asyncio.run(breaker.call(failing_func))

        # Circuit should now be open
        assert breaker.state == CircuitState.OPEN

        # Next call should be rejected immediately
        with pytest.raises(CircuitBreakerOpenException):
            asyncio.run(breaker.call(failing_func))

    def test_half_open_after_timeout(self):
        """Circuit should transition to HALF_OPEN after recovery timeout"""
        breaker = CircuitBreaker(
            "test",
            failure_threshold=1,
            recovery_timeout_seconds=1
        )

        async def failing_func():
            raise ValueError("Test error")

        # Cause failure
        with pytest.raises(ValueError):
            asyncio.run(breaker.call(failing_func))

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        asyncio.run(asyncio.sleep(1.1))

        # Try calling again - should transition to HALF_OPEN
        async def succeeding_func():
            return "success"

        result = asyncio.run(breaker.call(succeeding_func))
        assert result == "success"
        assert breaker.state == CircuitState.HALF_OPEN

    def test_closes_after_success_in_half_open(self):
        """Circuit should close after successful calls in HALF_OPEN"""
        breaker = CircuitBreaker(
            "test",
            failure_threshold=1,
            recovery_timeout_seconds=1,
            success_threshold_half_open=2
        )

        async def failing_func():
            raise ValueError("Test error")

        async def succeeding_func():
            return "success"

        # Open circuit
        with pytest.raises(ValueError):
            asyncio.run(breaker.call(failing_func))

        # Artificially set to HALF_OPEN
        breaker._transition_to(CircuitState.HALF_OPEN)

        # Two successes should close circuit
        for _ in range(2):
            asyncio.run(breaker.call(succeeding_func))

        assert breaker.state == CircuitState.CLOSED


class TestCircuitBreakerFailureHandling:
    """Test failure detection and handling"""

    def test_resets_failure_count_on_success(self):
        """Failure count should reset on successful call"""
        breaker = CircuitBreaker("test", failure_threshold=3)

        async def failing_func():
            raise ValueError("Test error")

        async def succeeding_func():
            return "success"

        # Cause 2 failures
        for _ in range(2):
            with pytest.raises(ValueError):
                asyncio.run(breaker.call(failing_func))

        assert breaker.failure_count == 2

        # Success should reset counter
        asyncio.run(breaker.call(succeeding_func))
        assert breaker.failure_count == 0

    def test_only_counts_expected_exceptions(self):
        """Should only count configured exception types"""
        breaker = CircuitBreaker(
            "test",
            failure_threshold=3,
            expected_exception=ValueError
        )

        async def raises_type_error():
            raise TypeError("Wrong exception")

        # TypeError should not be counted
        with pytest.raises(TypeError):
            asyncio.run(breaker.call(raises_type_error))

        assert breaker.failure_count == 0

    def test_counts_expected_exceptions(self):
        """Should count expected exception types"""
        breaker = CircuitBreaker(
            "test",
            failure_threshold=1,
            expected_exception=ValueError
        )

        async def raises_value_error():
            raise ValueError("Test error")

        # ValueError should be counted
        with pytest.raises(ValueError):
            asyncio.run(breaker.call(raises_value_error))

        assert breaker.failure_count == 1


class TestCircuitBreakerMetrics:
    """Test metrics and observability"""

    def test_get_metrics(self):
        """Should provide current metrics"""
        breaker = CircuitBreaker("test_breaker")
        metrics = breaker.get_metrics()

        assert metrics["name"] == "test_breaker"
        assert metrics["state"] == CircuitState.CLOSED.value
        assert metrics["failure_count"] == 0
        assert "failure_threshold" in metrics

    def test_metrics_after_failures(self):
        """Metrics should reflect failure state"""
        breaker = CircuitBreaker("test", failure_threshold=5)

        async def failing_func():
            raise ValueError("Test error")

        # Cause 3 failures
        for _ in range(3):
            with pytest.raises(ValueError):
                asyncio.run(breaker.call(failing_func))

        metrics = breaker.get_metrics()
        assert metrics["failure_count"] == 3
        assert metrics["state"] == CircuitState.CLOSED.value  # Not open yet


class TestCircuitBreakerManager:
    """Test managing multiple circuit breakers"""

    def test_register_and_retrieve_breakers(self):
        """Should manage multiple circuit breakers"""
        from agentmesh.infrastructure.resilience.circuit_breaker import CircuitBreakerManager

        manager = CircuitBreakerManager()

        breaker1 = CircuitBreaker("api_1")
        breaker2 = CircuitBreaker("api_2")

        manager.register("api_1", breaker1)
        manager.register("api_2", breaker2)

        assert manager.get("api_1") == breaker1
        assert manager.get("api_2") == breaker2

    def test_get_all_metrics(self):
        """Should aggregate metrics from all breakers"""
        from agentmesh.infrastructure.resilience.circuit_breaker import CircuitBreakerManager

        manager = CircuitBreakerManager()

        breaker1 = CircuitBreaker("api_1")
        breaker2 = CircuitBreaker("api_2")

        manager.register("api_1", breaker1)
        manager.register("api_2", breaker2)

        all_metrics = manager.get_all_metrics()

        assert "api_1" in all_metrics
        assert "api_2" in all_metrics
        assert all_metrics["api_1"]["name"] == "api_1"
        assert all_metrics["api_2"]["name"] == "api_2"

    def test_get_open_circuits(self):
        """Should identify open circuits"""
        from agentmesh.infrastructure.resilience.circuit_breaker import CircuitBreakerManager

        manager = CircuitBreakerManager()

        breaker1 = CircuitBreaker("api_1", failure_threshold=1)
        breaker2 = CircuitBreaker("api_2")

        manager.register("api_1", breaker1)
        manager.register("api_2", breaker2)

        # Open api_1
        async def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            asyncio.run(breaker1.call(failing_func))

        open_circuits = manager.get_open_circuits()
        assert "api_1" in open_circuits
        assert "api_2" not in open_circuits
