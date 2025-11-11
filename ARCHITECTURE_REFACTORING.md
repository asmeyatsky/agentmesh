# AgentMesh Architecture Refactoring Plan

## Executive Summary

This document outlines a comprehensive refactoring strategy to transform AgentMesh into an enterprise-grade, agentic system that strictly adheres to the architectural principles defined in `claude.md` (based on DDD, Clean Architecture, and Hexagonal Architecture patterns).

**Goals:**
1. Fix critical security and architectural issues
2. Achieve strict separation of concerns across all layers
3. Implement DDD and CQRS patterns consistently
4. Make the system truly agentic with autonomous agents
5. Achieve 80%+ test coverage
6. Document all architectural decisions

---

## Phase 1: Critical Fixes (Week 1)

### 1.1 Security Issue: Hardcoded Encryption Key

**Current Issue:**
- Location: `agentmesh/security/encryption.py:8`
- Problem: Encryption key is hardcoded placeholder
- Severity: CRITICAL

**Refactoring Strategy:**
```python
# BEFORE (WRONG):
ENCRYPTION_KEY = b'YOUR_SECURE_KEY_HERE_32_CHARACTERS'

# AFTER (CORRECT):
# Use environment variables or key management service
from pydantic_settings import BaseSettings

class SecurityConfig(BaseSettings):
    encryption_key: str  # Load from environment
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

# In encryption.py
config = SecurityConfig()
cipher_suite = Fernet(config.encryption_key.encode())
```

**Architectural Principle:** Rule 5 (Documentation) + Infrastructure layer patterns

**Tasks:**
- [ ] Create `EncryptionPort` interface in domain/ports
- [ ] Create `EnvironmentVariableEncryptionAdapter` in infrastructure
- [ ] Update encryption.py to use port interface
- [ ] Add to docker-compose and deployment docs

---

### 1.2 Remove Database Access from MessageRouter

**Current Issue:**
- Location: `agentmesh/mal/router.py:47-61`
- Problem: Router has direct database access (violates SRP)
- Severity: HIGH

**Refactoring Strategy:**

```
Current (WRONG):
┌──────────────┐
│ MessageRouter│─────────┐
└──────────────┘         │
                         ▼
                    ┌─────────┐
                    │ Database│
                    └─────────┘

After (CORRECT):
┌──────────────┐         ┌────────────────────┐
│ MessageRouter│────────▶│ TenantRepositoryPort│
└──────────────┘         └────────────────────┘
                                 △
                                 │
                         ┌───────┴──────────┐
                         ▼                  ▼
                   PostgreSQL         InMemory(Test)
```

**Implementation:**
```python
# agentmesh/domain/ports/tenant_repository_port.py
from abc import ABC, abstractmethod
from typing import Optional, List

class TenantRepositoryPort(ABC):
    @abstractmethod
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        pass

    @abstractmethod
    async def get_tenant_by_api_key(self, api_key: str) -> Optional[Tenant]:
        """Get tenant by API key"""
        pass

# agentmesh/infrastructure/repositories/postgres_tenant_repository.py
class PostgresTenantRepository(TenantRepositoryPort):
    def __init__(self, db_session):
        self.db = db_session

    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        # Database implementation
        pass

# agentmesh/mal/router.py (REFACTORED)
class MessageRouter:
    def __init__(self,
                 tenant_repository: TenantRepositoryPort,
                 message_broker: MessagePlatformAdapter):
        self.tenant_repo = tenant_repository  # Inject port
        self.broker = message_broker

    async def route_message(self, message: UniversalMessage):
        # Use port instead of direct DB access
        tenant = await self.tenant_repo.get_tenant(message.tenant_id)
        # ... rest of logic
```

**Architectural Principles:**
- Separation of Concerns (SoC)
- Interface-First Development (Rule 2)
- Dependency Injection

**Tasks:**
- [ ] Create `TenantRepositoryPort` in domain/ports
- [ ] Create `PostgresTenantRepository` in infrastructure
- [ ] Create `InMemoryTenantRepository` for testing
- [ ] Refactor MessageRouter to use injection
- [ ] Add dependency injection container configuration
- [ ] Update tests with mock repository

---

### 1.3 Fix Incomplete Implementations

**Current Issues:**

**Issue 3A: AdvancedRouter** (`mal/advanced_router.py`)
- References undefined `LoadBalancer` class
- Methods are incomplete stubs

**Issue 3B: BackupService** (`dr/backup_service.py`)
- All methods are placeholders with only logging

**Refactoring Strategy:**

```python
# agentmesh/domain/services/agent_load_balancer_service.py
@dataclass(frozen=True)
class AgentCapability(ValueObject):
    name: str
    proficiency_level: int  # 1-5

@dataclass(frozen=True)
class AgentMetrics(ValueObject):
    current_load: float  # 0-100%
    response_time_ms: float
    success_rate: float  # 0-1
    last_health_check: datetime

class AgentLoadBalancerService(DomainService):
    """
    Selects best agent based on capabilities and load.

    Invariants:
    - Only considers healthy agents
    - Prioritizes agents with matching capabilities
    - Distributes load evenly across equally-capable agents
    """

    def select_agent(self,
                    required_capabilities: List[str],
                    available_agents: List[Agent],
                    metrics: Dict[str, AgentMetrics]) -> Optional[Agent]:
        """
        Selects best agent for task.

        Algorithm:
        1. Filter agents with all required capabilities
        2. Filter out unhealthy agents
        3. Score by: load (60%), success_rate (30%), response_time (10%)
        4. Return agent with highest score
        """
        candidates = self._filter_capable_agents(required_capabilities, available_agents)
        healthy = self._filter_healthy_agents(candidates, metrics)

        if not healthy:
            return None

        return max(healthy, key=lambda a: self._calculate_score(a, metrics))

# agnetmesh/domain/ports/backup_port.py
class BackupPort(ABC):
    @abstractmethod
    async def create_backup(self, tenant_id: str, data: Dict) -> str:
        """Create backup, return backup_id"""
        pass

    @abstractmethod
    async def restore_backup(self, backup_id: str) -> Dict:
        """Restore backup by ID"""
        pass

# agentmesh/infrastructure/adapters/s3_backup_adapter.py
class S3BackupAdapter(BackupPort):
    def __init__(self, s3_client, bucket_name: str):
        self.s3 = s3_client
        self.bucket = bucket_name

    async def create_backup(self, tenant_id: str, data: Dict) -> str:
        backup_id = f"{tenant_id}-{datetime.now().isoformat()}"
        await self.s3.put_object(
            Bucket=self.bucket,
            Key=f"backups/{backup_id}",
            Body=json.dumps(data)
        )
        return backup_id
```

**Architectural Principles:**
- Clean Architecture (infrastructure layer)
- Ports & Adapters (Rule 2)
- Domain Services vs Infrastructure

**Tasks:**
- [ ] Create `AgentLoadBalancerService` domain service
- [ ] Create `BackupPort` in domain/ports
- [ ] Implement `S3BackupAdapter` in infrastructure
- [ ] Implement `PostgresBackupAdapter` in infrastructure
- [ ] Refactor AdvancedRouter to use domain service
- [ ] Remove placeholder BackupService
- [ ] Add comprehensive tests

---

## Phase 2: Domain-Driven Design (Week 2-3)

### 2.1 Create Rich Domain Models

**Bounded Context: Agent Management**

```python
# agentmesh/domain/entities/agent_aggregate.py
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import List, Set

@dataclass(frozen=True)
class AgentCapability(ValueObject):
    """Value Object: Agent capability with proficiency level"""
    name: str
    proficiency_level: int  # 1-5

    def __post_init__(self):
        if not 1 <= self.proficiency_level <= 5:
            raise ValueError("Proficiency must be 1-5")

@dataclass(frozen=True)
class AgentId(ValueObject):
    """Value Object: Agent identity"""
    value: str

    def __post_init__(self):
        if not self.value or len(self.value) < 3:
            raise ValueError("Agent ID must be non-empty")

@dataclass(frozen=True)
class AgentStatus(ValueObject):
    """Value Object: Agent status enumeration"""
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    PAUSED = "PAUSED"
    TERMINATED = "TERMINATED"

@dataclass(frozen=True)
class AgentAggregate:
    """
    Agent Aggregate Root

    Invariants:
    - Agent must have unique ID within tenant
    - Agent must have at least one capability
    - Status must be valid enum value
    - Resource requirements must be non-negative
    - Health check timeout must be positive
    """
    agent_id: AgentId
    tenant_id: str
    name: str
    capabilities: List[AgentCapability]
    status: str = AgentStatus.AVAILABLE
    resource_requirements: Dict[str, float] = field(default_factory=dict)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    health_check_timeout_seconds: int = 30
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self.capabilities:
            raise ValueError("Agent must have at least one capability")
        if self.health_check_timeout_seconds <= 0:
            raise ValueError("Health check timeout must be positive")

    def mark_healthy(self) -> 'AgentAggregate':
        """Record successful heartbeat"""
        return replace(self, last_heartbeat=datetime.now())

    def is_healthy(self, timeout_seconds: Optional[int] = None) -> bool:
        """Check if agent is responding"""
        timeout = timeout_seconds or self.health_check_timeout_seconds
        elapsed = (datetime.now() - self.last_heartbeat).total_seconds()
        return elapsed < timeout

    def assign_task(self) -> 'AgentAggregate':
        """Transition to BUSY state"""
        if self.status != AgentStatus.AVAILABLE:
            raise ValueError(f"Cannot assign task to {self.status} agent")
        return replace(self, status=AgentStatus.BUSY)

    def complete_task(self) -> 'AgentAggregate':
        """Transition back to AVAILABLE"""
        return replace(self, status=AgentStatus.AVAILABLE)

    def pause(self) -> 'AgentAggregate':
        """Pause agent operations"""
        return replace(self, status=AgentStatus.PAUSED)

    def resume(self) -> 'AgentAggregate':
        """Resume agent operations"""
        return replace(self, status=AgentStatus.AVAILABLE)

    def terminate(self) -> 'AgentAggregate':
        """Permanently terminate agent"""
        return replace(self, status=AgentStatus.TERMINATED)

    def has_capability(self, capability_name: str) -> bool:
        """Check if agent has specific capability"""
        return any(c.name == capability_name for c in self.capabilities)

# agentmesh/domain/domain_events/agent_events.py
@dataclass(frozen=True)
class AgentCreatedEvent(DomainEvent):
    """Event: Agent was created"""
    agent_id: str
    tenant_id: str
    capabilities: List[str]
    created_at: datetime

@dataclass(frozen=True)
class AgentTaskAssignedEvent(DomainEvent):
    """Event: Task assigned to agent"""
    agent_id: str
    task_id: str
    assigned_at: datetime

@dataclass(frozen=True)
class AgentTaskCompletedEvent(DomainEvent):
    """Event: Agent completed task"""
    agent_id: str
    task_id: str
    result: Dict
    completed_at: datetime

@dataclass(frozen=True)
class AgentHealthCheckFailedEvent(DomainEvent):
    """Event: Agent failed health check"""
    agent_id: str
    failed_at: datetime
    last_seen: datetime
```

**Bounded Context: Message Routing**

```python
# agentmesh/domain/entities/message_aggregate.py
@dataclass(frozen=True)
class MessageId(ValueObject):
    value: str

@dataclass(frozen=True)
class MessagePriority(ValueObject):
    """Value Object for message priority"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass(frozen=True)
class RouteTarget(ValueObject):
    """Value Object representing a routing target"""
    agent_id: str
    queue_name: str
    required_capabilities: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class MessageAggregate:
    """
    Message Aggregate Root

    Invariants:
    - Message must have at least one target
    - Priority must be valid (1-4)
    - Payload must not exceed size limit
    - Created timestamp must not be in future
    """
    message_id: MessageId
    tenant_id: str
    source_agent_id: str
    targets: List[RouteTarget]
    payload: Dict
    priority: int = MessagePriority.NORMAL
    correlation_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    status: str = "CREATED"  # CREATED, ROUTED, DELIVERED, FAILED

    def __post_init__(self):
        if not self.targets:
            raise ValueError("Message must have at least one target")
        if not MessagePriority.LOW <= self.priority <= MessagePriority.CRITICAL:
            raise ValueError("Invalid priority")
        if self.created_at > datetime.now():
            raise ValueError("Created timestamp cannot be in future")

    def mark_routed(self) -> 'MessageAggregate':
        """Mark message as routed to broker"""
        return replace(self, status="ROUTED")

    def mark_delivered(self) -> 'MessageAggregate':
        """Mark message as delivered to target"""
        return replace(self, status="DELIVERED")

    def mark_failed(self) -> 'MessageAggregate':
        """Mark message as failed"""
        return replace(self, status="FAILED")

    def is_expired(self) -> bool:
        """Check if message has expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
```

**Architectural Principles:**
- Rule 3: Immutable Domain Models
- Rich business logic in entities
- Value Objects for type safety

**Tasks:**
- [ ] Create value objects: AgentCapability, AgentId, MessageId
- [ ] Create AgentAggregate with all methods
- [ ] Create MessageAggregate with state transitions
- [ ] Create domain events
- [ ] Add invariant validation
- [ ] Create domain service: AgentLoadBalancerService
- [ ] Create domain service: MessageRoutingService
- [ ] Add comprehensive unit tests for all entities

---

### 2.2 Create Port Interfaces

```python
# agentmesh/domain/ports/agent_repository_port.py
class AgentRepositoryPort(ABC):
    @abstractmethod
    async def save(self, agent: AgentAggregate) -> None:
        """Save/update agent"""
        pass

    @abstractmethod
    async def get_by_id(self, agent_id: str, tenant_id: str) -> Optional[AgentAggregate]:
        """Get agent by ID within tenant"""
        pass

    @abstractmethod
    async def find_by_capabilities(self,
                                   capabilities: List[str],
                                   tenant_id: str) -> List[AgentAggregate]:
        """Find agents with specific capabilities"""
        pass

    @abstractmethod
    async def find_all(self, tenant_id: str) -> List[AgentAggregate]:
        """Find all agents for tenant"""
        pass

# agentmesh/domain/ports/message_broker_port.py
class MessageBrokerPort(ABC):
    @abstractmethod
    async def publish(self,
                     message: MessageAggregate,
                     topic: str) -> str:
        """Publish message, return delivery ID"""
        pass

    @abstractmethod
    async def subscribe(self,
                       topic: str,
                       callback: Callable[[MessageAggregate], None]) -> str:
        """Subscribe to topic, return subscription ID"""
        pass

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from topic"""
        pass

# agentmesh/domain/ports/event_store_port.py
class EventStorePort(ABC):
    @abstractmethod
    async def append_events(self,
                           aggregate_id: str,
                           events: List[DomainEvent]) -> None:
        """Append events to event stream"""
        pass

    @abstractmethod
    async def get_events(self,
                        aggregate_id: str,
                        from_version: int = 0) -> List[DomainEvent]:
        """Get events for aggregate"""
        pass
```

**Tasks:**
- [ ] Create all port interfaces in domain/ports
- [ ] Document port contracts and invariants
- [ ] Create mock implementations for testing

---

### 2.3 Create Application Layer Use Cases

```python
# agentmesh/application/use_cases/create_agent_use_case.py
@dataclass
class CreateAgentDTO:
    """Input DTO"""
    agent_id: str
    tenant_id: str
    name: str
    capabilities: List[Dict[str, Any]]  # [{"name": "...", "level": 1}]
    metadata: Dict[str, str]

@dataclass
class AgentCreatedDTO:
    """Output DTO"""
    agent_id: str
    tenant_id: str
    status: str

class CreateAgentUseCase:
    """
    Use Case: Create new agent

    Architectural Intent:
    - Orchestrates domain logic for agent creation
    - Publishes AgentCreatedEvent for other bounded contexts
    - Validates input through domain invariants
    """

    def __init__(self,
                 agent_repository: AgentRepositoryPort,
                 event_store: EventStorePort,
                 event_bus: EventBus):
        self.agent_repo = agent_repository
        self.event_store = event_store
        self.event_bus = event_bus

    async def execute(self, dto: CreateAgentDTO) -> AgentCreatedDTO:
        # Reconstruct from domain
        try:
            capabilities = [
                AgentCapability(
                    name=cap["name"],
                    proficiency_level=cap.get("level", 1)
                )
                for cap in dto.capabilities
            ]

            agent = AgentAggregate(
                agent_id=AgentId(dto.agent_id),
                tenant_id=dto.tenant_id,
                name=dto.name,
                capabilities=capabilities,
                metadata=dto.metadata
            )

            # Save to repository
            await self.agent_repo.save(agent)

            # Publish event
            event = AgentCreatedEvent(
                aggregate_id=dto.agent_id,
                agent_id=dto.agent_id,
                tenant_id=dto.tenant_id,
                capabilities=[c.name for c in capabilities],
                created_at=datetime.now()
            )
            await self.event_store.append_events(dto.agent_id, [event])
            await self.event_bus.publish(event)

            return AgentCreatedDTO(
                agent_id=agent.agent_id.value,
                tenant_id=agent.tenant_id,
                status=agent.status
            )

        except ValueError as e:
            raise ApplicationException(f"Invalid agent data: {e}")

# agentmesh/application/use_cases/route_message_use_case.py
class RouteMessageUseCase:
    """
    Use Case: Route message to appropriate agents

    Architectural Intent:
    - Encapsulates message routing logic
    - Uses MessageRoutingService for intelligent routing
    - Maintains audit trail of routing decisions
    """

    def __init__(self,
                 agent_repo: AgentRepositoryPort,
                 message_broker: MessageBrokerPort,
                 routing_service: MessageRoutingService,
                 event_store: EventStorePort):
        self.agent_repo = agent_repo
        self.broker = message_broker
        self.routing_service = routing_service
        self.event_store = event_store

    async def execute(self, message: MessageAggregate) -> RouteResultDTO:
        # Find target agents
        targets = await self.routing_service.find_targets(
            message,
            await self.agent_repo.find_all(message.tenant_id)
        )

        # Publish to broker
        delivery_ids = []
        for target in targets:
            delivery_id = await self.broker.publish(message, target.queue_name)
            delivery_ids.append(delivery_id)

        # Record in event store
        routed_message = message.mark_routed()
        # ... store routing event

        return RouteResultDTO(
            message_id=message.message_id.value,
            target_count=len(targets),
            delivery_ids=delivery_ids
        )
```

**Architectural Principles:**
- Rule 1: Zero Business Logic in Infrastructure
- Orchestration of domain objects
- DTOs for input/output boundaries

**Tasks:**
- [ ] Create all use cases with proper orchestration
- [ ] Create input/output DTOs
- [ ] Add error handling and validation
- [ ] Create use case tests with mocked dependencies

---

## Phase 3: Making It Agentic (Week 3-4)

### 3.1 Autonomous Agent Decision Making

```python
# agentmesh/domain/services/agent_autonomy_service.py
@dataclass
class DecisionContext:
    """Context for agent decision making"""
    current_status: str
    available_tasks: List[Dict]
    agent_load: float
    system_load: float
    priority_threshold: int
    recent_performance: float

class AgentAutonomyService(DomainService):
    """
    Domain Service: Autonomous agent decision making

    Invariants:
    - Agent only takes actions within its capabilities
    - Decisions respect resource constraints
    - Actions logged for audit trail
    """

    def should_accept_task(self,
                          agent: AgentAggregate,
                          task: Dict,
                          context: DecisionContext) -> bool:
        """
        Decide if agent should accept task.

        Decision factors:
        1. Does agent have required capabilities?
        2. Is agent overloaded?
        3. Is task priority appropriate?
        4. Recent success rate?
        """
        # Check capabilities
        required_caps = task.get("required_capabilities", [])
        if not all(agent.has_capability(cap) for cap in required_caps):
            return False

        # Check load
        if context.agent_load > 0.8:  # 80% loaded
            if task.get("priority", 2) < context.priority_threshold:
                return False  # Don't take low-priority if overloaded

        # Check recent performance
        if context.recent_performance < 0.5:  # <50% success rate
            if task.get("priority", 2) <= 1:  # Low priority
                return False

        return True

    def prioritize_tasks(self,
                        tasks: List[Dict],
                        agent_capabilities: List[str]) -> List[Dict]:
        """
        Prioritize available tasks for agent.

        Scoring: priority (40%) + capability_match (30%) + deadline (20%) + complexity (10%)
        """
        def score_task(task):
            priority_score = task.get("priority", 2) / 4 * 0.4
            capability_match = len(set(task.get("required_capabilities", []))
                                 & set(agent_capabilities)) * 0.3
            deadline_score = self._score_deadline(task.get("deadline")) * 0.2
            complexity_score = min(task.get("complexity", 1) / 10, 1) * 0.1
            return priority_score + capability_match + deadline_score + complexity_score

        return sorted(tasks, key=score_task, reverse=True)

# agentmesh/aol/autonomous_agent.py
class AutonomousAgent(Agent):
    """
    Autonomous Agent: Makes decisions independently

    Capabilities:
    - Task selection and prioritization
    - Dynamic load management
    - Performance self-assessment
    - Safety constraint checking
    """

    def __init__(self,
                 agent_aggregate: AgentAggregate,
                 autonomy_service: AgentAutonomyService,
                 safety_monitor: SafetyMonitor,
                 message_broker: MessageBrokerPort):
        super().__init__()
        self.aggregate = agent_aggregate
        self.autonomy = autonomy_service
        self.safety = safety_monitor
        self.broker = message_broker
        self.current_load = 0.0
        self.completed_tasks = 0
        self.failed_tasks = 0

    async def process_task_offers(self, task_offers: List[Dict]):
        """
        Autonomously decide which tasks to accept.
        """
        decision_context = DecisionContext(
            current_status=self.aggregate.status,
            available_tasks=task_offers,
            agent_load=self.current_load,
            system_load=await self._get_system_load(),
            priority_threshold=2,
            recent_performance=self._calculate_success_rate()
        )

        # Get prioritized list
        prioritized = self.autonomy.prioritize_tasks(
            task_offers,
            [c.name for c in self.aggregate.capabilities]
        )

        # Accept tasks autonomously
        accepted = []
        for task in prioritized:
            if self.autonomy.should_accept_task(self.aggregate, task, decision_context):
                accepted.append(task)
                self.current_load += task.get("estimated_load", 0.1)

                # Safety check before acceptance
                if not await self.safety.can_execute_task(task, self.aggregate.tenant_id):
                    continue  # Skip unsafe tasks

                # Send acceptance message
                await self.broker.publish(
                    MessageAggregate(
                        message_id=MessageId(str(uuid4())),
                        tenant_id=self.aggregate.tenant_id,
                        source_agent_id=self.aggregate.agent_id.value,
                        targets=[RouteTarget(agent_id="coordinator", queue_name="coordinator.tasks")],
                        payload={"action": "TASK_ACCEPTED", "task_id": task["id"]},
                        correlation_id=task.get("correlation_id")
                    ),
                    "coordinator.responses"
                )

                if len(accepted) >= 3:  # Limit concurrent tasks
                    break

    def _calculate_success_rate(self) -> float:
        """Calculate success rate from task history"""
        total = self.completed_tasks + self.failed_tasks
        if total == 0:
            return 1.0
        return self.completed_tasks / total
```

**Architectural Principles:**
- DDD: Domain Services for complex logic
- Immutable Aggregates: Make decisions, return new state
- Separation: Autonomy service separate from agent implementation
- Event-driven: Publish decisions as events

**Tasks:**
- [ ] Create AgentAutonomyService
- [ ] Create AutonomousAgent with decision-making
- [ ] Create task prioritization logic
- [ ] Add safety constraint checking
- [ ] Create load management
- [ ] Add performance tracking
- [ ] Create comprehensive tests

---

### 3.2 Multi-Agent Coordination Patterns

```python
# agentmesh/domain/services/agent_collaboration_service.py
class AgentCollaborationService(DomainService):
    """
    Domain Service: Coordinate multiple agents for complex tasks

    Implements patterns:
    - Task decomposition: Break complex tasks into subtasks
    - Resource negotiation: Agents negotiate for resources
    - Knowledge sharing: Agents exchange insights
    - Conflict resolution: Handle conflicting decisions
    """

    async def decompose_complex_task(self,
                                     task: Dict,
                                     available_agents: List[AgentAggregate]) -> List[Dict]:
        """
        Break complex task into subtasks optimized for available agents.

        Algorithm:
        1. Analyze task dependencies
        2. Identify natural decomposition points
        3. Assign subtasks to agents based on capabilities
        4. Schedule task execution
        """
        dependencies = task.get("dependencies", {})
        subtasks = task.get("subtasks", [])

        # Build dependency graph
        dag = self._build_dependency_dag(dependencies)

        # Topological sort for execution order
        ordered_subtasks = self._topological_sort(dag)

        # Assign agents to subtasks
        assignments = {}
        for subtask in ordered_subtasks:
            best_agent = self._select_best_agent_for_subtask(
                subtask,
                available_agents
            )
            if best_agent:
                assignments[subtask["id"]] = best_agent.agent_id.value

        # Annotate subtasks with assignments
        for subtask in ordered_subtasks:
            if subtask["id"] in assignments:
                subtask["assigned_to"] = assignments[subtask["id"]]
            else:
                raise ValueError(f"Could not find agent for subtask {subtask['id']}")

        return ordered_subtasks

    async def coordinate_agent_negotiation(self,
                                          agents: List[AgentAggregate],
                                          resource_needs: Dict) -> Dict:
        """
        Facilitate agents negotiating for shared resources.

        Returns allocation plan that satisfies needs and constraints.
        """
        # Use auction mechanism or bilateral negotiation
        allocation = {}
        for agent_id, need in resource_needs.items():
            allocation[agent_id] = await self._allocate_resources(agent_id, need, agents)
        return allocation

    async def resolve_agent_conflicts(self,
                                     agents: List[AgentAggregate],
                                     conflict_actions: List[Dict]) -> Dict:
        """
        Resolve conflicting actions from multiple agents.

        Strategies:
        - Priority-based: Higher priority action wins
        - Time-based: First action wins
        - Consensus: Agents negotiate resolution
        """
        # Implement conflict detection and resolution
        resolved = {}
        for conflict in conflict_actions:
            # TODO: Implement resolution strategy
            pass
        return resolved

# agentmesh/aol/collaborative_agent.py
class CollaborativeAgent(AutonomousAgent):
    """
    Collaborative Agent: Works with other agents

    Capabilities:
    - Request help from other agents
    - Share results and insights
    - Participate in voting/consensus
    - Negotiate resource allocation
    """

    def __init__(self,
                 agent_aggregate: AgentAggregate,
                 collaboration_service: AgentCollaborationService,
                 message_broker: MessageBrokerPort,
                 **kwargs):
        super().__init__(agent_aggregate, **kwargs)
        self.collaboration = collaboration_service

    async def request_help(self, task_id: str, assistance_needed: str):
        """Request help from agents with specific capabilities"""
        message = MessageAggregate(
            message_id=MessageId(str(uuid4())),
            tenant_id=self.aggregate.tenant_id,
            source_agent_id=self.aggregate.agent_id.value,
            targets=[RouteTarget(agent_id="*", queue_name="help.requests")],
            payload={
                "action": "HELP_REQUEST",
                "task_id": task_id,
                "assistance": assistance_needed,
                "required_capabilities": assistance_needed.split(",")
            },
            correlation_id=task_id
        )
        await self.broker.publish(message, "help.requests")

    async def share_results(self, task_id: str, results: Dict, target_agents: List[str]):
        """Share task results with other agents"""
        message = MessageAggregate(
            message_id=MessageId(str(uuid4())),
            tenant_id=self.aggregate.tenant_id,
            source_agent_id=self.aggregate.agent_id.value,
            targets=[RouteTarget(agent_id=a, queue_name=f"agent.{a}.results") for a in target_agents],
            payload={
                "action": "SHARE_RESULTS",
                "task_id": task_id,
                "results": results
            },
            correlation_id=task_id
        )
        await self.broker.publish(message, "results.shared")
```

**Tasks:**
- [ ] Create AgentCollaborationService
- [ ] Create CollaborativeAgent
- [ ] Implement task decomposition
- [ ] Implement resource negotiation
- [ ] Implement conflict resolution
- [ ] Create comprehensive tests

---

## Phase 4: Testing & Documentation (Week 4)

### 4.1 Comprehensive Test Suite

```python
# tests/unit/domain/entities/test_agent_aggregate.py
class TestAgentAggregate:
    """Unit tests for AgentAggregate domain model"""

    def test_agent_creation_with_valid_data(self):
        agent = AgentAggregate(
            agent_id=AgentId("agent-1"),
            tenant_id="tenant-1",
            name="Data Processor",
            capabilities=[AgentCapability("data_processing", 4)],
            resource_requirements={"cpu": 2, "memory": 4}
        )
        assert agent.status == AgentStatus.AVAILABLE
        assert len(agent.capabilities) == 1

    def test_agent_creation_fails_without_capabilities(self):
        with pytest.raises(ValueError):
            AgentAggregate(
                agent_id=AgentId("agent-1"),
                tenant_id="tenant-1",
                name="Bad Agent",
                capabilities=[]
            )

    def test_agent_marks_healthy_on_heartbeat(self):
        agent = AgentAggregate(
            agent_id=AgentId("agent-1"),
            tenant_id="tenant-1",
            name="Test Agent",
            capabilities=[AgentCapability("test", 1)],
            last_heartbeat=datetime.now() - timedelta(seconds=60)
        )

        # Initially unhealthy (60 seconds ago)
        assert not agent.is_healthy()

        # After heartbeat, healthy
        healthy_agent = agent.mark_healthy()
        assert healthy_agent.is_healthy()

    def test_agent_state_transitions(self):
        agent = AgentAggregate(
            agent_id=AgentId("agent-1"),
            tenant_id="tenant-1",
            name="Test Agent",
            capabilities=[AgentCapability("test", 1)]
        )

        # AVAILABLE -> BUSY
        busy = agent.assign_task()
        assert busy.status == AgentStatus.BUSY

        # BUSY -> AVAILABLE
        available = busy.complete_task()
        assert available.status == AgentStatus.AVAILABLE

        # AVAILABLE -> PAUSED
        paused = available.pause()
        assert paused.status == AgentStatus.PAUSED

        # PAUSED -> AVAILABLE
        resumed = paused.resume()
        assert resumed.status == AgentStatus.AVAILABLE

    def test_cannot_assign_task_to_non_available_agent(self):
        agent = AgentAggregate(
            agent_id=AgentId("agent-1"),
            tenant_id="tenant-1",
            name="Test Agent",
            capabilities=[AgentCapability("test", 1)]
        )
        busy_agent = agent.assign_task()

        with pytest.raises(ValueError):
            busy_agent.assign_task()

# tests/integration/application/test_create_agent_use_case.py
@pytest.mark.asyncio
class TestCreateAgentUseCase:
    """Integration tests for CreateAgentUseCase"""

    @pytest.fixture
    def setup(self):
        agent_repo = InMemoryAgentRepository()
        event_store = InMemoryEventStore()
        event_bus = EventBus()
        use_case = CreateAgentUseCase(agent_repo, event_store, event_bus)
        return use_case, agent_repo, event_store, event_bus

    async def test_create_agent_successfully(self, setup):
        use_case, repo, store, bus = setup

        dto = CreateAgentDTO(
            agent_id="agent-1",
            tenant_id="tenant-1",
            name="Data Processor",
            capabilities=[{"name": "data_processing", "level": 4}],
            metadata={}
        )

        result = await use_case.execute(dto)

        assert result.agent_id == "agent-1"
        assert result.status == AgentStatus.AVAILABLE

        # Verify saved to repository
        saved = await repo.get_by_id("agent-1", "tenant-1")
        assert saved is not None
        assert saved.name == "Data Processor"

        # Verify event published
        events = await store.get_events("agent-1")
        assert len(events) == 1
        assert isinstance(events[0], AgentCreatedEvent)

# tests/e2e/test_agent_workflow.py
@pytest.mark.asyncio
class TestAgentWorkflow:
    """End-to-end tests for agent workflows"""

    async def test_complete_task_execution_workflow(self):
        """Test: Agent accepts task -> executes -> reports results"""
        # Setup
        agent = await setup_test_agent("data-processor-1")
        task = create_test_task("process-data", ["data_processing"])

        # Execute
        accepted = await agent.process_task_offers([task])
        assert len(accepted) > 0

        # Simulate execution
        await asyncio.sleep(0.1)

        # Verify completion
        history = await agent.get_task_history()
        assert len(history) == 1
        assert history[0]["status"] == "COMPLETED"
```

**Tasks:**
- [ ] Create unit tests for all domain models
- [ ] Create integration tests for use cases
- [ ] Create end-to-end tests for workflows
- [ ] Aim for 80%+ code coverage
- [ ] Setup coverage reporting

### 4.2 Documentation

```markdown
# AgentMesh Architecture Documentation

## Design Overview

### Architectural Pattern: Clean/Hexagonal Architecture
- **Domain Layer**: Core business logic, free of frameworks
- **Application Layer**: Use cases, orchestration
- **Infrastructure Layer**: Database, messaging, external services
- **Presentation Layer**: API, CLI, UI

### Bounded Contexts
1. **Agent Management**: Agent lifecycle, capabilities, health
2. **Message Routing**: Message delivery, routing decisions
3. **Task Coordination**: Task assignment, execution, completion
4. **Safety & Alignment**: Policy enforcement, monitoring
5. **Observability**: Metrics, logging, tracing

## Key Design Decisions

### 1. Immutable Aggregates
**Decision**: All domain aggregates are frozen dataclasses
**Rationale**: Prevents accidental state corruption, enables event sourcing, easier to reason about
**Trade-offs**: Requires creating new instances for state changes (minimal performance impact)

### 2. Port-Based External Integrations
**Decision**: All external dependencies (DB, messaging, etc.) are behind port interfaces
**Rationale**: Supports multiple implementations, testability, framework independence
**Trade-offs**: Additional abstraction layer (minimal complexity)

### 3. Autonomous Agent Decision Making
**Decision**: Agents make their own task acceptance/prioritization decisions
**Rationale**: Reduces centralized bottleneck, improves responsiveness, enables true multi-agent autonomy
**Trade-offs**: Requires safety constraints, distributed consensus mechanisms

## Testing Strategy
- Unit: Domain models, services (fast, isolated)
- Integration: Use cases, adapter implementations (slower, cross-component)
- E2E: Complete workflows (slowest, full system)
- Coverage target: 80%+

## Deployment
- Docker Compose for development/testing
- Kubernetes-ready with 12-factor app principles
- Environment-based configuration
- Graceful shutdown handling
```

**Tasks:**
- [ ] Write module documentation
- [ ] Create architecture decision records (ADRs)
- [ ] Document design patterns used
- [ ] Create troubleshooting guide
- [ ] Document configuration options

---

## Implementation Timeline

| Phase | Week | Focus | Key Deliverables |
|-------|------|-------|------------------|
| **1** | W1 | Critical Fixes | Security fixes, remove coupling, complete implementations |
| **2** | W2-W3 | DDD & Architecture | Domain models, ports, use cases, services |
| **3** | W3-W4 | Agentic Features | Autonomous decisions, collaboration, coordination |
| **4** | W4 | Testing & Docs | 80% coverage, comprehensive documentation |

---

## Success Criteria

### Code Quality
- [ ] All 5 non-negotiable rules followed (Rule 1-5)
- [ ] 80%+ test coverage
- [ ] Zero hardcoded secrets
- [ ] Strict layer separation
- [ ] No business logic in infrastructure

### Agentic Capabilities
- [ ] Agents make autonomous decisions
- [ ] Multi-agent coordination working
- [ ] Conflict resolution implemented
- [ ] Safety constraints enforced
- [ ] Collaborative task execution

### Documentation
- [ ] All modules documented with intent
- [ ] Design decisions recorded
- [ ] Architecture diagrams included
- [ ] Troubleshooting guides provided
- [ ] Configuration options documented

---

## Next Steps

1. Review this plan with stakeholders
2. Create feature branches for each phase
3. Start Phase 1 implementation
4. Weekly progress reviews
5. Continuous testing throughout

---

**Document Version**: 1.0
**Last Updated**: 2024
**Author**: Claude Code
**Status**: Ready for Implementation
