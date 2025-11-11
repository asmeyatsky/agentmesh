"""
Distributed Tracing Context Management

Manages trace context propagation across distributed systems using OpenTelemetry.
Enables full visibility into cross-service calls and message flows.

Architectural Intent:
- Automatic trace context propagation to all messages
- Span management for operation tracking
- Context preservation across async boundaries
- Integration with message aggregates for audit trail
"""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import replace
from typing import Optional, Dict, Any
from datetime import datetime

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, Tracer


class TracingContext:
    """
    Manages distributed tracing context for operations.

    Handles:
    - Creating and managing spans
    - Propagating trace context to messages
    - Tracking operation duration and status
    - Recording operation outcomes
    """

    def __init__(self):
        """Initialize tracing context"""
        self.tracer: Tracer = trace.get_tracer(__name__)

    @asynccontextmanager
    async def trace_operation(self,
                             operation_name: str,
                             attributes: Optional[Dict[str, Any]] = None,
                             include_result: bool = False):
        """
        Context manager for traced operations.

        Usage:
            async with tracing.trace_operation("route_message", {
                "message_id": msg.id,
                "tenant_id": msg.tenant_id
            }) as span:
                result = await router.route(msg)
                span.set_attribute("target_count", len(result.targets))

        Args:
            operation_name: Name of the operation
            attributes: Initial span attributes
            include_result: If True, yield span for result recording

        Yields:
            Span object for custom attribute recording
        """
        with self.tracer.start_as_current_span(operation_name) as span:
            # Set initial attributes
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))

            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    def get_current_trace_context(self) -> Dict[str, str]:
        """
        Get current trace context as dictionary.

        Returns:
            Dictionary with trace_id, span_id, and trace_flags
        """
        span = trace.get_current_span()
        context = span.get_span_context()

        return {
            "trace_id": format(context.trace_id, '032x'),
            "span_id": format(context.span_id, '016x'),
            "trace_flags": str(context.trace_flags),
            "is_remote": str(context.is_remote)
        }

    def add_trace_context_to_message(self,
                                    message: Any,
                                    trace_key: str = "trace_context") -> Any:
        """
        Add trace context to message metadata.

        Args:
            message: Message aggregate to annotate
            trace_key: Key to use in metadata

        Returns:
            Message with trace context added to metadata
        """
        context = self.get_current_trace_context()

        # Assuming message has metadata field and replace method
        return replace(message,
            metadata={
                **(message.metadata if hasattr(message, 'metadata') else {}),
                trace_key: context
            }
        )

    def record_operation_result(self,
                               operation_name: str,
                               duration_ms: float,
                               success: bool,
                               result_details: Optional[Dict] = None):
        """
        Record operation result for observability.

        Args:
            operation_name: Name of operation
            duration_ms: Duration in milliseconds
            success: Whether operation succeeded
            result_details: Additional details to record
        """
        span = trace.get_current_span()

        # Set operation metrics
        span.set_attribute("operation.duration_ms", duration_ms)
        span.set_attribute("operation.success", success)

        if result_details:
            for key, value in result_details.items():
                span.set_attribute(f"result.{key}", str(value))

    async def trace_async_operation(self,
                                   operation_name: str,
                                   func,
                                   *args,
                                   attributes: Optional[Dict[str, Any]] = None,
                                   **kwargs) -> Any:
        """
        Trace an async function call.

        Args:
            operation_name: Name for the span
            func: Async function to call
            attributes: Span attributes
            args: Function arguments
            kwargs: Function keyword arguments

        Returns:
            Function result
        """
        async with self.trace_operation(operation_name, attributes) as span:
            return await func(*args, **kwargs)

    def create_child_span(self,
                         operation_name: str,
                         attributes: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a child span in current context.

        Args:
            operation_name: Name of child operation
            attributes: Span attributes

        Returns:
            New span context manager
        """
        return self.trace_operation(operation_name, attributes)

    @staticmethod
    def create_span_from_headers(headers: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        Extract trace context from HTTP/message headers.

        Supports W3C Trace Context standard.

        Args:
            headers: Request/message headers

        Returns:
            Extracted trace context or None
        """
        traceparent = headers.get('traceparent')
        if not traceparent:
            return None

        # Parse W3C traceparent format: version-trace_id-span_id-trace_flags
        parts = traceparent.split('-')
        if len(parts) < 4:
            return None

        return {
            "trace_id": parts[1],
            "parent_span_id": parts[2],
            "trace_flags": parts[3]
        }


class RequestIdContext:
    """
    Manages request ID context for correlation.

    Provides:
    - Request ID generation and propagation
    - Correlation with trace IDs
    - Request lifecycle tracking
    """

    def __init__(self):
        """Initialize request context"""
        self._request_id = asyncio.current_task()

    @staticmethod
    def generate_request_id() -> str:
        """Generate unique request ID"""
        from uuid import uuid4
        return str(uuid4())

    @staticmethod
    def get_or_create_request_id() -> str:
        """Get current request ID or create new one"""
        # Implementation would use context vars
        from uuid import uuid4
        return str(uuid4())

    @staticmethod
    def correlate_with_trace(request_id: str, trace_context: Dict[str, str]) -> Dict[str, str]:
        """
        Correlate request ID with trace context.

        Args:
            request_id: Request identifier
            trace_context: Trace context from tracing

        Returns:
            Combined correlation context
        """
        return {
            "request_id": request_id,
            **trace_context
        }
