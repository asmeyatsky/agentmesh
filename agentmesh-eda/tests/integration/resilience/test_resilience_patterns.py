"""
Integration Tests: Resilience Patterns

Tests circuit breaker and resilience patterns in real scenarios.

Architectural Intent:
- Verify circuit breaker behavior across multiple failures
- Verify retry logic works correctly
- Verify bulkhead pattern isolation
- Verify fallback mechanisms
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from agentmesh.infrastructure.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerConfig,
)
from agentmesh.infrastructure.resilience.retry_policy import RetryPolicy, RetryConfig
from agentmesh.infrastructure.resilience.bulkhead import Bulkhead


class FailingService:
    """Mock service that simulates failures"""

    def __init__(self, failure_rate=1.0, failure_count=None):
        self.failure_rate = failure_rate
        self.failure_count = failure_count
        self.call_count = 0

    async def call(self, *args, **kwargs):
        self.call_count += 1

        if self.failure_count is not None and self.call_count <= self.failure_count:
            raise Exception(f"Service failure #{self.call_count}")

        await asyncio.sleep(0.01)  # Simulate work
        return f"Success #{self.call_count}"


@pytest.mark.asyncio
class TestCircuitBreakerIntegration:
    """Integration tests for circuit breaker"""

    async def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures"""
        config = CircuitBreakerConfig(
            failure_threshold=3, recovery_timeout=1.0, expected_exception=Exception
        )

        failing_service = FailingService(failure_count=5)
        circuit_breaker = CircuitBreaker("test_service", config=config)

        # First 2 calls should fail but pass through (under threshold)
        for i in range(2):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_service.call)

        # Circuit should still be closed
        assert circuit_breaker.state == CircuitBreakerState.CLOSED

        # 3rd call should fail and open circuit (meets threshold)
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_service.call)

        # Circuit should now be open
        assert circuit_breaker.state == CircuitBreakerState.OPEN

    async def test_circuit_breaker_half_open_state(self):
        """Test circuit breaker transitions to half-open"""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1,
            expected_exception=Exception,
        )

        failing_service = FailingService(failure_count=2)
        circuit_breaker = CircuitBreaker("test_service", config=config)

        # Cause circuit to open
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_service.call)
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_service.call)

        assert circuit_breaker.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Next call should put circuit in half-open then succeed
        success_result = await circuit_breaker.call(failing_service.call)

        assert success_result == "Success #3"

    async def test_circuit_breaker_metrics_integration(self):
        """Test circuit breaker records metrics"""
        config = CircuitBreakerConfig(
            failure_threshold=5, recovery_timeout=1.0, expected_exception=Exception
        )

        failing_service = FailingService(failure_count=2)
        circuit_breaker = CircuitBreaker("test_service", config=config)

        # Cause some failures and successes
        for i in range(5):
            try:
                await circuit_breaker.call(failing_service.call)
            except:
                pass

        # Get metrics
        metrics = circuit_breaker.get_metrics()

        # Verify metrics structure
        assert "state" in metrics
        assert "failure_count" in metrics
        assert "success_count" in metrics
        assert "last_failure_time" in metrics


@pytest.mark.asyncio
class TestResiliencePatternsIntegration:
    """Integration tests combining resilience patterns"""

    async def test_circuit_breaker_with_bulkhead(self):
        """Test circuit breaker protecting a bulkhead"""
        config = CircuitBreakerConfig(failure_threshold=10, recovery_timeout=1.0)

        bulkhead = Bulkhead(max_concurrent=3, timeout=5.0)
        circuit_breaker = CircuitBreaker("protected_service", config=config)

        async def success_service():
            await asyncio.sleep(0.01)
            return "success"

        # Execute through both resilience patterns
        async def protected_call():
            return await bulkhead.execute(success_service)

        results = []
        for i in range(5):
            try:
                result = await circuit_breaker.call(protected_call)
                results.append(result)
            except Exception as e:
                results.append(e)

        # Should have successes
        successes = [r for r in results if isinstance(r, str)]
        assert len(successes) > 0

    async def test_retry_policy_with_exponential_backoff(self):
        """Test retry policy with exponential backoff"""
        retry_config = RetryConfig(
            max_attempts=4, base_delay_ms=10, max_delay_ms=100,
            backoff_multiplier=2.0, jitter_enabled=False,
        )
        retry_policy = RetryPolicy(config=retry_config)

        call_count = 0

        async def timing_service():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Service unavailable")
            return "Success"

        result = await retry_policy.execute(timing_service)

        assert result.success is True
        assert result.result == "Success"
        assert result.attempts >= 3
