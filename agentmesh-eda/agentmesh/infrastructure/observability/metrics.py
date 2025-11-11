"""
Prometheus Metrics for AgentMesh

Implements comprehensive metrics collection for:
- Message routing performance
- Agent health and activity
- Task execution metrics
- System resource utilization
- Business KPIs

Architectural Intent:
- All metrics use consistent naming conventions (agentmesh_* prefix)
- Labels enable multi-dimensional analysis
- Histogram buckets optimized for typical latencies
- Metrics are immutable once registered (thread-safe)
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from enum import Enum
from typing import Optional


class MetricLabels(Enum):
    """Standard metric labels for consistency"""
    TENANT_ID = "tenant_id"
    MESSAGE_TYPE = "message_type"
    ROUTING_STRATEGY = "routing_strategy"
    AGENT_ID = "agent_id"
    AGENT_STATUS = "status"
    TASK_TYPE = "task_type"
    TASK_STATUS = "task_status"
    FAILURE_REASON = "failure_reason"
    CAPABILITY = "capability"


class AgentMeshMetrics:
    """
    Prometheus metrics collection for AgentMesh.

    All metrics are registered as class attributes for thread-safety
    and to enable easy discovery of available metrics.
    """

    # ===== MESSAGE ROUTING METRICS =====

    # Counter: total messages routed
    messages_routed_total = Counter(
        'agentmesh_messages_routed_total',
        'Total number of messages routed',
        ['tenant_id', 'message_type', 'routing_strategy']
    )

    # Histogram: message routing latency
    routing_latency_seconds = Histogram(
        'agentmesh_message_routing_latency_seconds',
        'Message routing latency in seconds',
        ['routing_strategy', 'tenant_id'],
        buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5)
    )

    # Counter: routing errors
    routing_errors_total = Counter(
        'agentmesh_routing_errors_total',
        'Total message routing errors',
        ['tenant_id', 'error_type']
    )

    # Gauge: messages in queue
    messages_in_queue = Gauge(
        'agentmesh_messages_in_queue',
        'Number of messages currently in queue',
        ['tenant_id', 'queue_name']
    )

    # ===== AGENT METRICS =====

    # Gauge: active agents
    active_agents = Gauge(
        'agentmesh_active_agents',
        'Number of active agents by status',
        ['tenant_id', 'status']
    )

    # Counter: agent state transitions
    agent_state_changes_total = Counter(
        'agentmesh_agent_state_changes_total',
        'Total agent state transitions',
        ['agent_id', 'from_status', 'to_status']
    )

    # Counter: health check failures
    health_check_failures_total = Counter(
        'agentmesh_health_check_failures_total',
        'Total agent health check failures',
        ['agent_id', 'failure_reason']
    )

    # Histogram: health check duration
    health_check_duration_seconds = Histogram(
        'agentmesh_health_check_duration_seconds',
        'Agent health check duration',
        ['agent_id'],
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0)
    )

    # Gauge: agent load
    agent_load_percent = Gauge(
        'agentmesh_agent_load_percent',
        'Agent current load percentage (0-100)',
        ['agent_id']
    )

    # Gauge: agent capability coverage
    agent_capability_coverage = Gauge(
        'agentmesh_agent_capability_coverage',
        'Capability coverage across all agents',
        ['tenant_id', 'capability']
    )

    # ===== TASK EXECUTION METRICS =====

    # Histogram: task execution time
    task_execution_seconds = Histogram(
        'agentmesh_task_execution_seconds',
        'Task execution time in seconds',
        ['agent_id', 'task_type'],
        buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
    )

    # Counter: task outcomes
    tasks_completed_total = Counter(
        'agentmesh_tasks_completed_total',
        'Total completed tasks by status',
        ['agent_id', 'task_type', 'task_status']
    )

    # Counter: task failures
    task_failures_total = Counter(
        'agentmesh_task_failures_total',
        'Total task failures',
        ['agent_id', 'task_type', 'failure_reason']
    )

    # Gauge: tasks in progress
    tasks_in_progress = Gauge(
        'agentmesh_tasks_in_progress',
        'Number of tasks currently in progress',
        ['tenant_id', 'agent_id']
    )

    # ===== SYSTEM RESOURCE METRICS =====

    # Gauge: database connections
    db_connections_active = Gauge(
        'agentmesh_db_connections_active',
        'Active database connections'
    )

    # Gauge: cache hit rate
    cache_hit_rate = Gauge(
        'agentmesh_cache_hit_rate',
        'Cache hit rate percentage',
        ['cache_type']
    )

    # Histogram: database query duration
    db_query_duration_seconds = Histogram(
        'agentmesh_db_query_duration_seconds',
        'Database query duration',
        ['query_type'],
        buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0)
    )

    # ===== BUSINESS KPIs =====

    # Counter: agents created
    agents_created_total = Counter(
        'agentmesh_agents_created_total',
        'Total agents created',
        ['tenant_id']
    )

    # Counter: agents terminated
    agents_terminated_total = Counter(
        'agentmesh_agents_terminated_total',
        'Total agents terminated',
        ['tenant_id']
    )

    # Gauge: tenant agents
    tenant_agents_total = Gauge(
        'agentmesh_tenant_agents_total',
        'Total agents per tenant',
        ['tenant_id']
    )

    # Counter: collaboration events
    collaboration_events_total = Counter(
        'agentmesh_collaboration_events_total',
        'Total multi-agent collaboration events',
        ['tenant_id', 'event_type']
    )

    # ===== ERROR & ANOMALY METRICS =====

    # Counter: critical errors
    critical_errors_total = Counter(
        'agentmesh_critical_errors_total',
        'Total critical errors',
        ['error_type', 'component']
    )

    # Gauge: error rate
    error_rate = Gauge(
        'agentmesh_error_rate',
        'Current error rate',
        ['component']
    )

    # ===== SERVICE INFO =====

    service_info = Info(
        'agentmesh_info',
        'AgentMesh service information',
        labelnames=['version', 'environment', 'commit']
    )

    @classmethod
    def record_message_routed(cls,
                             tenant_id: str,
                             message_type: str,
                             routing_strategy: str = "default"):
        """Record message routing event"""
        cls.messages_routed_total.labels(
            tenant_id=tenant_id,
            message_type=message_type,
            routing_strategy=routing_strategy
        ).inc()

    @classmethod
    def record_routing_latency(cls,
                              latency_seconds: float,
                              routing_strategy: str,
                              tenant_id: str):
        """Record routing latency"""
        cls.routing_latency_seconds.labels(
            routing_strategy=routing_strategy,
            tenant_id=tenant_id
        ).observe(latency_seconds)

    @classmethod
    def record_routing_error(cls,
                            tenant_id: str,
                            error_type: str):
        """Record routing error"""
        cls.routing_errors_total.labels(
            tenant_id=tenant_id,
            error_type=error_type
        ).inc()

    @classmethod
    def set_active_agents(cls,
                         tenant_id: str,
                         status: str,
                         count: int):
        """Set gauge for active agents"""
        cls.active_agents.labels(
            tenant_id=tenant_id,
            status=status
        ).set(count)

    @classmethod
    def record_health_check_failure(cls,
                                   agent_id: str,
                                   failure_reason: str):
        """Record agent health check failure"""
        cls.health_check_failures_total.labels(
            agent_id=agent_id,
            failure_reason=failure_reason
        ).inc()

    @classmethod
    def record_task_execution(cls,
                             duration_seconds: float,
                             agent_id: str,
                             task_type: str):
        """Record task execution time"""
        cls.task_execution_seconds.labels(
            agent_id=agent_id,
            task_type=task_type
        ).observe(duration_seconds)

    @classmethod
    def record_task_completion(cls,
                              agent_id: str,
                              task_type: str,
                              status: str):
        """Record task completion"""
        cls.tasks_completed_total.labels(
            agent_id=agent_id,
            task_type=task_type,
            task_status=status
        ).inc()

    @classmethod
    def set_agent_load(cls,
                      agent_id: str,
                      load_percent: float):
        """Set agent load gauge"""
        cls.agent_load_percent.labels(
            agent_id=agent_id
        ).set(min(load_percent, 100.0))

    @classmethod
    def record_agent_created(cls, tenant_id: str):
        """Record agent creation"""
        cls.agents_created_total.labels(tenant_id=tenant_id).inc()
        cls.tenant_agents_total.labels(tenant_id=tenant_id).inc()

    @classmethod
    def record_agent_terminated(cls, tenant_id: str):
        """Record agent termination"""
        cls.agents_terminated_total.labels(tenant_id=tenant_id).inc()
        # Decrement tenant_agents_total handled separately due to gauge limitations
