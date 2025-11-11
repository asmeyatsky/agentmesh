"""
Circuit Breaker Pattern Implementation

Prevents cascading failures by stopping requests to failing services.

States:
- CLOSED: Normal operation, requests go through
- OPEN: Service failing, reject all requests
- HALF_OPEN: Testing if service recovered, allow limited requests

Architectural Intent:
- Fail fast when upstream service is down
- Automatic recovery detection
- Observable state transitions
- Integration with observability (metrics, logging)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Callable, Any, Awaitable


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Service failing, reject requests
    HALF_OPEN = "half_open"    # Testing recovery, allow limited requests


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit is open"""
    pass


class CircuitBreakerException(Exception):
    """General circuit breaker exception"""
    pass


class CircuitBreaker:
    """
    Circuit breaker for service resilience.

    Protects against cascading failures by:
    - Monitoring call success/failure rates
    - Opening circuit when failure threshold exceeded
    - Automatically testing recovery
    - Recording metrics for observability
    """

    def __init__(self,
                 name: str,
                 failure_threshold: int = 5,
                 recovery_timeout_seconds: int = 60,
                 expected_exception: type = Exception,
                 success_threshold_half_open: int = 2):
        """
        Initialize circuit breaker

        Args:
            name: Circuit breaker identifier
            failure_threshold: Failures before opening circuit
            recovery_timeout_seconds: Time before attempting recovery
            expected_exception: Exception type to count as failure
            success_threshold_half_open: Successes to close circuit from HALF_OPEN
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.expected_exception = expected_exception
        self.success_threshold_half_open = success_threshold_half_open

        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None

        self.logger = logging.getLogger(f"circuit_breaker.{name}")

    async def call(self,
                   func: Callable[..., Awaitable[Any]],
                   *args,
                   **kwargs) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Async function to execute
            args: Function arguments
            kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenException: If circuit is open
            Exception: If function fails
        """
        # Check if circuit should open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to(CircuitState.HALF_OPEN)
            else:
                self._record_open_rejection()
                raise CircuitBreakerOpenException(
                    f"Circuit breaker '{self.name}' is OPEN"
                )

        # Execute function
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def call_sync(self,
                  func: Callable[..., Any],
                  *args,
                  **kwargs) -> Any:
        """
        Execute synchronous function through circuit breaker.

        Args:
            func: Sync function to execute
            args: Function arguments
            kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenException: If circuit is open
            Exception: If function fails
        """
        # Check if circuit should open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to(CircuitState.HALF_OPEN)
            else:
                self._record_open_rejection()
                raise CircuitBreakerOpenException(
                    f"Circuit breaker '{self.name}' is OPEN"
                )

        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call"""
        # Reset failure count when in CLOSED state
        if self.state == CircuitState.CLOSED:
            self.failure_count = 0

        # Track recovery progress in HALF_OPEN state
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold_half_open:
                self._transition_to(CircuitState.CLOSED)

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        # Transition to OPEN if threshold exceeded
        if self.failure_count >= self.failure_threshold:
            self._transition_to(CircuitState.OPEN)

        # Reset recovery progress in HALF_OPEN state
        if self.state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)

    def _should_attempt_reset(self) -> bool:
        """Check if recovery timeout has elapsed"""
        if self.last_failure_time is None:
            return False

        elapsed = datetime.utcnow() - self.last_failure_time
        timeout = timedelta(seconds=self.recovery_timeout_seconds)
        return elapsed >= timeout

    def _transition_to(self, new_state: CircuitState):
        """Transition to new state with logging"""
        old_state = self.state
        self.state = new_state

        # Reset counters for new state
        if new_state == CircuitState.CLOSED:
            self.failure_count = 0
            self.success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self.success_count = 0

        self.logger.warning(
            f"Circuit breaker '{self.name}' transitioned from {old_state.value} "
            f"to {new_state.value}"
        )

    def _record_open_rejection(self):
        """Record rejection due to open circuit"""
        self.logger.debug(
            f"Request rejected: circuit breaker '{self.name}' is OPEN"
        )

    def get_state(self) -> CircuitState:
        """Get current circuit state"""
        return self.state

    def get_metrics(self) -> dict:
        """Get circuit breaker metrics"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout_seconds": self.recovery_timeout_seconds
        }


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers.

    Provides:
    - Centralized circuit breaker management
    - Metrics aggregation
    - Bulk operations
    """

    def __init__(self):
        """Initialize circuit breaker manager"""
        self.breakers: dict[str, CircuitBreaker] = {}

    def register(self,
                 name: str,
                 breaker: CircuitBreaker) -> CircuitBreaker:
        """Register circuit breaker"""
        self.breakers[name] = breaker
        return breaker

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self.breakers.get(name)

    def get_all_metrics(self) -> dict:
        """Get metrics for all circuit breakers"""
        return {
            name: breaker.get_metrics()
            for name, breaker in self.breakers.items()
        }

    def get_open_circuits(self) -> list[str]:
        """Get names of open circuits"""
        return [
            name for name, breaker in self.breakers.items()
            if breaker.get_state() == CircuitState.OPEN
        ]

    def reset_all(self):
        """Reset all circuit breakers to CLOSED"""
        for breaker in self.breakers.values():
            breaker._transition_to(CircuitState.CLOSED)
