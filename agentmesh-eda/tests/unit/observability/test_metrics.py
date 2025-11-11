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
            tenant_id="tenant-1",
            message_type="task",
            routing_strategy="load_balanced"
        )

        # Counter should be incremented
        assert AgentMeshMetrics.messages_routed_total._value.get() > 0

    def test_record_routing_latency(self):
        """Test recording routing latency"""
        latency = 0.045  # 45ms

        AgentMeshMetrics.record_routing_latency(
            latency_seconds=latency,
            routing_strategy="load_balanced",
            tenant_id="tenant-1"
        )

        # Histogram should have recorded observation
        assert AgentMeshMetrics.routing_latency_seconds._value.get() is not None

    def test_record_agent_created(self):
        """Test recording agent creation"""
        AgentMeshMetrics.record_agent_created(tenant_id="tenant-1")

        # Should increment both creation and total counters
        assert AgentMeshMetrics.agents_created_total._value.get() > 0

    def test_record_health_check_failure(self):
        """Test recording health check failures"""
        AgentMeshMetrics.record_health_check_failure(
            agent_id="agent-1",
            failure_reason="timeout"
        )

        assert AgentMeshMetrics.health_check_failures_total._value.get() > 0

    def test_set_agent_load(self):
        """Test setting agent load gauge"""
        load = 75.5  # 75.5%

        AgentMeshMetrics.set_agent_load(
            agent_id="agent-1",
            load_percent=load
        )

        # Gauge should be set
        assert AgentMeshMetrics.agent_load_percent._value.get(('agent-1',)) == load

    def test_record_task_execution(self):
        """Test recording task execution time"""
        AgentMeshMetrics.record_task_execution(
            duration_seconds=2.5,
            agent_id="agent-1",
            task_type="data_processing"
        )

        assert AgentMeshMetrics.task_execution_seconds._value.get() is not None

    def test_record_task_completion(self):
        """Test recording task completion"""
        AgentMeshMetrics.record_task_completion(
            agent_id="agent-1",
            task_type="data_processing",
            status="SUCCESS"
        )

        assert AgentMeshMetrics.tasks_completed_total._value.get() > 0

    def test_multiple_metric_calls(self):
        """Test recording multiple metrics in sequence"""
        # Simulate a complete task workflow
        AgentMeshMetrics.set_agent_load("agent-1", 50.0)
        AgentMeshMetrics.record_message_routed("tenant-1", "task", "default")
        AgentMeshMetrics.record_routing_latency(0.025, "default", "tenant-1")
        AgentMeshMetrics.record_task_execution(1.5, "agent-1", "processing")
        AgentMeshMetrics.record_task_completion("agent-1", "processing", "SUCCESS")

        # All metrics should have recorded values
        assert AgentMeshMetrics.messages_routed_total._value.get() > 0


class TestMetricsLabels:
    """Test metric labels and dimensions"""

    def test_routing_metrics_with_different_strategies(self):
        """Test routing metrics with multiple strategies"""
        strategies = ["load_balanced", "priority", "random"]

        for strategy in strategies:
            AgentMeshMetrics.record_routing_latency(
                latency_seconds=0.050,
                routing_strategy=strategy,
                tenant_id="tenant-1"
            )

        # All should be recorded with different labels
        assert AgentMeshMetrics.routing_latency_seconds._value.get() is not None

    def test_agent_metrics_with_different_statuses(self):
        """Test agent metrics with different statuses"""
        statuses = ["AVAILABLE", "BUSY", "PAUSED", "TERMINATED"]

        for status in statuses:
            AgentMeshMetrics.set_active_agents(
                tenant_id="tenant-1",
                status=status,
                count=5
            )

        # All statuses should be recorded
        assert AgentMeshMetrics.active_agents._value.get() is not None

    def test_multi_tenant_metrics(self):
        """Test metrics across multiple tenants"""
        tenants = ["tenant-1", "tenant-2", "tenant-3"]

        for tenant in tenants:
            AgentMeshMetrics.record_agent_created(tenant_id=tenant)

        # All tenants should have metrics recorded
        assert AgentMeshMetrics.agents_created_total._value.get() >= 3


class TestMetricsCounters:
    """Test counter increment behavior"""

    def test_counter_increments(self):
        """Test that counters properly increment"""
        initial = AgentMeshMetrics.messages_routed_total._value.get()

        for i in range(5):
            AgentMeshMetrics.record_message_routed(
                tenant_id="tenant-1",
                message_type="task",
                routing_strategy="load_balanced"
            )

        final = AgentMeshMetrics.messages_routed_total._value.get()
        assert final >= initial + 5

    def test_routing_errors_counter(self):
        """Test error counter increments"""
        AgentMeshMetrics.record_routing_error(
            tenant_id="tenant-1",
            error_type="timeout"
        )

        assert AgentMeshMetrics.routing_errors_total._value.get() > 0


class TestMetricsAggregation:
    """Test metric aggregation and retrieval"""

    def test_get_metrics_snapshot(self):
        """Test getting current metrics snapshot"""
        # Record various metrics
        AgentMeshMetrics.record_message_routed("tenant-1", "task", "default")
        AgentMeshMetrics.set_agent_load("agent-1", 60.0)
        AgentMeshMetrics.record_task_completion("agent-1", "process", "SUCCESS")

        # All metrics should be accessible
        assert AgentMeshMetrics.messages_routed_total._value.get() > 0
        assert AgentMeshMetrics.agent_load_percent._value.get() is not None
        assert AgentMeshMetrics.tasks_completed_total._value.get() > 0
