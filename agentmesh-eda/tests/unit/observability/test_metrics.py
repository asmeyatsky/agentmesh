"""
Unit tests for Prometheus metrics collection.

Tests:
- Metric recording for all operations
- Label combinations
- Metric state and counters
"""

import pytest
from agentmesh.infrastructure.observability.metrics import AgentMeshMetrics


class TestMetricsRecording:
    """Test metrics recording functionality"""

    def test_record_message_routed(self):
        """Test recording message routing metrics"""
        # Record metric
        AgentMeshMetrics.record_message_routed(
            tenant_id="tenant-1", message_type="task", routing_strategy="load_balanced"
        )

        # Check that metric exists and is callable (indicates it's working)
        assert AgentMeshMetrics.messages_routed_total is not None
        # Should be able to call again without error
        AgentMeshMetrics.record_message_routed(
            tenant_id="tenant-1", message_type="task", routing_strategy="load_balanced"
        )

    def test_record_routing_latency(self):
        """Test recording routing latency"""
        latency = 0.045  # 45ms

        AgentMeshMetrics.record_routing_latency(
            latency_seconds=latency,
            routing_strategy="load_balanced",
            tenant_id="tenant-1",
        )

        # Should be able to call without error
        assert AgentMeshMetrics.routing_latency_seconds is not None
        # Call again to ensure no error
        AgentMeshMetrics.record_routing_latency(
            latency_seconds=latency,
            routing_strategy="load_balanced",
            tenant_id="tenant-1",
        )

    def test_record_agent_created(self):
        """Test recording agent creation"""
        AgentMeshMetrics.record_agent_created(tenant_id="tenant-1")

        # Should be able to call without error
        assert AgentMeshMetrics.agents_created_total is not None
        # Call again to ensure no error
        AgentMeshMetrics.record_agent_created(tenant_id="tenant-1")

    def test_record_health_check_failure(self):
        """Test recording health check failures"""
        AgentMeshMetrics.record_health_check_failure(
            agent_id="agent-1", failure_reason="timeout"
        )

        # Should be able to call without error
        assert AgentMeshMetrics.health_check_failures_total is not None
        # Call again to ensure no error
        AgentMeshMetrics.record_health_check_failure(
            agent_id="agent-1", failure_reason="timeout"
        )

    def test_set_agent_load(self):
        """Test setting agent load gauge"""
        load = 75.5

        AgentMeshMetrics.set_agent_load(agent_id="agent-1", load_percent=load)

        # Should be able to call without error
        assert AgentMeshMetrics.agent_load_percent is not None
        # Call again to ensure no error
        AgentMeshMetrics.set_agent_load(agent_id="agent-1", load_percent=80.0)

    def test_record_task_execution(self):
        """Test recording task execution time"""
        duration = 2.5  # seconds

        AgentMeshMetrics.record_task_execution(
            duration_seconds=duration, agent_id="agent-1", task_type="inference"
        )

        # Should be able to call without error
        assert AgentMeshMetrics.task_execution_seconds is not None
        # Call again to ensure no error
        AgentMeshMetrics.record_task_execution(
            duration_seconds=duration, agent_id="agent-1", task_type="inference"
        )

    def test_record_task_completion(self):
        """Test recording task completion"""
        AgentMeshMetrics.record_task_completion(
            agent_id="agent-1", task_type="inference", status="success"
        )

        # Should be able to call without error
        assert AgentMeshMetrics.tasks_completed_total is not None
        # Call again to ensure no error
        AgentMeshMetrics.record_task_completion(
            agent_id="agent-1", task_type="inference", status="success"
        )

    def test_multiple_metric_calls(self):
        """Test multiple metric calls don't interfere"""
        # Record multiple different metrics
        AgentMeshMetrics.record_message_routed(
            tenant_id="tenant-1", message_type="task", routing_strategy="load_balanced"
        )
        AgentMeshMetrics.record_agent_created(tenant_id="tenant-1")
        AgentMeshMetrics.set_agent_load(agent_id="agent-1", load_percent=50.0)

        # Should be able to call again without error
        AgentMeshMetrics.record_message_routed(
            tenant_id="tenant-1", message_type="task", routing_strategy="load_balanced"
        )


class TestMetricsLabels:
    """Test metric labels functionality"""

    def test_routing_metrics_with_different_strategies(self):
        """Test routing metrics with different strategy labels"""
        AgentMeshMetrics.record_routing_latency(
            latency_seconds=0.05, routing_strategy="round_robin", tenant_id="tenant-1"
        )

        AgentMeshMetrics.record_routing_latency(
            latency_seconds=0.1, routing_strategy="load_balanced", tenant_id="tenant-1"
        )

        # Should be able to call without error
        assert AgentMeshMetrics.routing_latency_seconds is not None

    def test_agent_metrics_with_different_statuses(self):
        """Test agent metrics with different status labels"""
        AgentMeshMetrics.set_active_agents(
            tenant_id="tenant-1", status="available", count=5
        )

        AgentMeshMetrics.set_active_agents(tenant_id="tenant-1", status="busy", count=2)

        # Should be able to call without error
        assert AgentMeshMetrics.active_agents is not None

    def test_multi_tenant_metrics(self):
        """Test metrics with different tenant labels"""
        for tenant_id in ["tenant-1", "tenant-2", "tenant-3"]:
            AgentMeshMetrics.record_agent_created(tenant_id=tenant_id)

        # Should be able to call without error
        assert AgentMeshMetrics.agents_created_total is not None


class TestMetricsCounters:
    """Test counter metrics"""

    def test_counter_increments(self):
        """Test that counters increment without error"""
        # Initial call
        AgentMeshMetrics.record_message_routed(
            tenant_id="tenant-1", message_type="task", routing_strategy="default"
        )

        # Multiple calls should work
        for _ in range(3):
            AgentMeshMetrics.record_message_routed(
                tenant_id="tenant-1", message_type="task", routing_strategy="default"
            )

        # Should be able to call without error
        assert AgentMeshMetrics.messages_routed_total is not None

    def test_routing_errors_counter(self):
        """Test routing errors counter"""
        AgentMeshMetrics.record_routing_error(
            tenant_id="tenant-1", error_type="timeout"
        )

        # Multiple error calls should work
        for _ in range(2):
            AgentMeshMetrics.record_routing_error(
                tenant_id="tenant-1", error_type="timeout"
            )

        # Should be able to call without error
        assert AgentMeshMetrics.routing_errors_total is not None


class TestMetricsAggregation:
    """Test metrics aggregation functionality"""

    def test_get_metrics_snapshot(self):
        """Test getting metrics snapshot"""
        # Record some metrics
        AgentMeshMetrics.record_message_routed(
            tenant_id="tenant-1", message_type="task", routing_strategy="load_balanced"
        )
        AgentMeshMetrics.record_agent_created(tenant_id="tenant-1")

        # Should be able to call without error
        assert AgentMeshMetrics.messages_routed_total is not None

        # All metric objects should be accessible
        assert hasattr(AgentMeshMetrics, "messages_routed_total")
        assert hasattr(AgentMeshMetrics, "agents_created_total")
        assert hasattr(AgentMeshMetrics, "routing_latency_seconds")
        assert hasattr(AgentMeshMetrics, "active_agents")
        assert hasattr(AgentMeshMetrics, "tasks_completed_total")


class TestMetricMethodsExist:
    """Test that all metric recording methods exist and are callable"""

    def test_all_metric_methods_exist(self):
        """Test that all expected methods exist"""
        methods = [
            "record_message_routed",
            "record_routing_latency",
            "record_routing_error",
            "set_active_agents",
            "record_health_check_failure",
            "record_task_execution",
            "record_task_completion",
            "set_agent_load",
            "record_agent_created",
            "record_agent_terminated",
        ]

        for method_name in methods:
            assert hasattr(AgentMeshMetrics, method_name)
            method = getattr(AgentMeshMetrics, method_name)
            assert callable(method)
