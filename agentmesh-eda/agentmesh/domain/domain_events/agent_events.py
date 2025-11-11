"""
Agent Domain Events

Architectural Intent:
- Represent important things that happen in the agent domain
- Enable event sourcing and event-driven architecture
- Allow other bounded contexts to react to agent changes
- Provide audit trail of agent lifecycle

Key Design Decisions:
1. Events are immutable (frozen dataclasses)
2. Base DomainEvent provides common attributes
3. Event versioning for backward compatibility
4. Timestamps in UTC for consistency
5. Minimal data in events (references, not full objects)

Domain Events:
- AgentCreatedEvent: New agent registered
- AgentActivatedEvent: Agent ready for operation
- AgentCapabilityAddedEvent: Agent gained new skill
- AgentTaskAssignedEvent: Task assigned to agent
- AgentTaskCompletedEvent: Agent completed task
- AgentTaskFailedEvent: Agent failed task
- AgentStatusChangedEvent: Agent status changed
- AgentHealthCheckPassedEvent: Agent passed health check
- AgentHealthCheckFailedEvent: Agent failed health check
- AgentTerminatedEvent: Agent removed from system
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, List


@dataclass(frozen=True)
class DomainEvent:
    """
    Base class for all domain events.

    Invariants:
    - aggregate_id identifies which aggregate this event belongs to
    - occurred_at is timestamp in UTC
    - event_id is unique identifier for this event
    """
    aggregate_id: str  # agent_id
    occurred_at: datetime
    event_id: str = field(default_factory=lambda: str(hash(datetime.utcnow())))
    version: str = "1.0"


@dataclass(frozen=True)
class AgentCreatedEvent(DomainEvent):
    """
    Event: Agent was created and registered in system.

    Triggered when: CreateAgentUseCase executes successfully
    Listened by: Agent registry, observability system
    """
    tenant_id: str
    agent_id: str
    name: str
    agent_type: str
    capabilities: List[str]
    metadata: Dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"AgentCreated(id={self.agent_id}, name={self.name}, caps={len(self.capabilities)})"


@dataclass(frozen=True)
class AgentActivatedEvent(DomainEvent):
    """
    Event: Agent activated and ready for operation.

    Triggered when: Agent.activate() is called
    Listened by: Agent registry, scheduling system
    """
    agent_id: str
    tenant_id: str
    activated_at: datetime

    def __str__(self) -> str:
        return f"AgentActivated(id={self.agent_id})"


@dataclass(frozen=True)
class AgentCapabilityAddedEvent(DomainEvent):
    """
    Event: Agent gained new capability.

    Triggered when: Agent.add_capability() is called
    Listened by: Agent registry, capability matcher
    """
    agent_id: str
    tenant_id: str
    capability_name: str
    proficiency_level: int

    def __str__(self) -> str:
        return f"AgentCapabilityAdded(id={self.agent_id}, cap={self.capability_name}, level={self.proficiency_level})"


@dataclass(frozen=True)
class AgentCapabilityUpgradedEvent(DomainEvent):
    """
    Event: Agent improved capability level.

    Triggered when: Agent.upgrade_capability() is called
    Listened by: Agent registry, performance analyzer
    """
    agent_id: str
    tenant_id: str
    capability_name: str
    from_level: int
    to_level: int

    def __str__(self) -> str:
        return f"AgentCapabilityUpgraded(id={self.agent_id}, cap={self.capability_name}, level={self.from_level}->{self.to_level})"


@dataclass(frozen=True)
class AgentTaskAssignedEvent(DomainEvent):
    """
    Event: Task was assigned to agent.

    Triggered when: Agent.assign_task() is called
    Listened by: Task tracking, performance metrics
    """
    agent_id: str
    tenant_id: str
    task_id: str
    assigned_at: datetime

    def __str__(self) -> str:
        return f"AgentTaskAssigned(agent={self.agent_id}, task={self.task_id})"


@dataclass(frozen=True)
class AgentTaskCompletedEvent(DomainEvent):
    """
    Event: Agent completed assigned task.

    Triggered when: Agent.complete_task() is called
    Listened by: Task tracking, metrics, next-agent notification
    """
    agent_id: str
    tenant_id: str
    task_id: str
    completed_at: datetime
    result: Dict = field(default_factory=dict)  # Task result/output
    execution_time_ms: int = 0  # How long task took

    def __str__(self) -> str:
        return f"AgentTaskCompleted(agent={self.agent_id}, task={self.task_id}, time={self.execution_time_ms}ms)"


@dataclass(frozen=True)
class AgentTaskFailedEvent(DomainEvent):
    """
    Event: Agent failed to complete assigned task.

    Triggered when: Agent.fail_task() is called
    Listened by: Task tracking, error handling, retry mechanism
    """
    agent_id: str
    tenant_id: str
    task_id: str
    failed_at: datetime
    error_message: str
    error_code: str = "UNKNOWN"

    def __str__(self) -> str:
        return f"AgentTaskFailed(agent={self.agent_id}, task={self.task_id}, error={self.error_code})"


@dataclass(frozen=True)
class AgentStatusChangedEvent(DomainEvent):
    """
    Event: Agent status changed (AVAILABLE -> BUSY -> AVAILABLE, etc).

    Triggered when: Any state transition occurs
    Listened by: Monitoring system, load balancer, UI
    """
    agent_id: str
    tenant_id: str
    from_status: str
    to_status: str
    changed_at: datetime
    reason: str = ""

    def __str__(self) -> str:
        return f"AgentStatusChanged(id={self.agent_id}, {self.from_status}->{self.to_status})"


@dataclass(frozen=True)
class AgentHealthCheckPassedEvent(DomainEvent):
    """
    Event: Agent passed health check (heartbeat received).

    Triggered when: Agent.mark_healthy() is called
    Listened by: Health monitoring, alerting system
    """
    agent_id: str
    tenant_id: str
    checked_at: datetime
    success_rate: float
    response_time_ms: float
    cpu_usage_percent: float
    memory_usage_percent: float

    def __str__(self) -> str:
        return f"AgentHealthCheckPassed(id={self.agent_id}, cpu={self.cpu_usage_percent}%, mem={self.memory_usage_percent}%)"


@dataclass(frozen=True)
class AgentHealthCheckFailedEvent(DomainEvent):
    """
    Event: Agent failed health check (heartbeat timeout).

    Triggered when: Agent.mark_unhealthy() is called
    Listened by: Alerting system, failover mechanism
    """
    agent_id: str
    tenant_id: str
    checked_at: datetime
    last_heartbeat: datetime
    timeout_seconds: int
    reason: str = "Heartbeat timeout"

    def __str__(self) -> str:
        return f"AgentHealthCheckFailed(id={self.agent_id}, reason={self.reason})"


@dataclass(frozen=True)
class AgentPausedEvent(DomainEvent):
    """
    Event: Agent was paused.

    Triggered when: Agent.pause() is called
    Listened by: Task scheduler, monitoring
    """
    agent_id: str
    tenant_id: str
    paused_at: datetime
    reason: str = ""

    def __str__(self) -> str:
        return f"AgentPaused(id={self.agent_id})"


@dataclass(frozen=True)
class AgentResumedEvent(DomainEvent):
    """
    Event: Agent was resumed.

    Triggered when: Agent.resume() is called
    Listened by: Task scheduler, monitoring
    """
    agent_id: str
    tenant_id: str
    resumed_at: datetime

    def __str__(self) -> str:
        return f"AgentResumed(id={self.agent_id})"


@dataclass(frozen=True)
class AgentTerminatedEvent(DomainEvent):
    """
    Event: Agent was terminated (removed from service).

    Triggered when: Agent.terminate() is called
    Listened by: Resource cleanup, monitoring, accounting
    """
    agent_id: str
    tenant_id: str
    terminated_at: datetime
    reason: str = ""
    tasks_completed: int = 0
    tasks_failed: int = 0

    def __str__(self) -> str:
        return f"AgentTerminated(id={self.agent_id}, completed={self.tasks_completed}, failed={self.tasks_failed})"
