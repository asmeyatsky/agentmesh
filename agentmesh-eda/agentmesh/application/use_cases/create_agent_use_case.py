"""
Create Agent Use Case

Architectural Intent:
- Orchestrates agent creation following domain rules
- Publishes domain events for other systems
- Handles cross-cutting concerns (logging, metrics)
- Separates business logic from infrastructure

Key Design Decisions:
1. Use case is synchronous (could be made async)
2. Returns DTO (not domain object) to consumers
3. Publishes events for event-driven integration
4. Validates input through domain invariants
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

from agentmesh.domain.entities.agent_aggregate import AgentAggregate
from agentmesh.domain.value_objects.agent_value_objects import (
    AgentId,
    AgentCapability,
    ResourceRequirement,
)
from agentmesh.domain.domain_events.agent_events import AgentCreatedEvent
from agentmesh.domain.ports.agent_repository_port import (
    AgentRepositoryPort,
)  # Will need to create
from agentmesh.cqrs.bus import EventBus
from agentmesh.cqrs.event import Event


@dataclass
class AgentCreatedCQRSWrapperEvent(Event):
    """Wrapper event for CQRS compatibility"""

    agent_created_event: AgentCreatedEvent

    def __init__(self, agent_created_event: AgentCreatedEvent):
        self.event_id = agent_created_event.event_id
        self.created_at = agent_created_event.occurred_at
        self.agent_created_event = agent_created_event


@dataclass
class CreateAgentDTO:
    """Input DTO: Data to create an agent"""

    tenant_id: str
    agent_id: str
    name: str
    agent_type: str = "generic"
    description: str = ""
    capabilities: List[Dict[str, int]] = (
        None  # [{"name": "task_processing", "level": 4}]
    )
    resource_requirements: Optional[Dict] = None
    metadata: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None


@dataclass
class AgentCreatedResultDTO:
    """Output DTO: Result of agent creation"""

    agent_id: str
    tenant_id: str
    name: str
    status: str
    created_at: datetime
    capabilities_count: int


class CreateAgentUseCase:
    """
    Use Case: Create new agent in system.

    Flow:
    1. Validate input DTO
    2. Create domain aggregate (validates business rules)
    3. Save to repository
    4. Publish domain event
    5. Return result DTO

    Returns:
        AgentCreatedResultDTO with agent details

    Raises:
        ValueError: If agent data is invalid
        Exception: If repository save fails
    """

    def __init__(self, agent_repository: AgentRepositoryPort, event_bus: EventBus):
        """
        Initialize use case with dependencies.

        Args:
            agent_repository: Port for persisting agents
            event_bus: Port for publishing events
        """
        self.agent_repo = agent_repository
        self.event_bus = event_bus
        logger.info("CreateAgentUseCase initialized")

    async def execute(self, dto: CreateAgentDTO) -> AgentCreatedResultDTO:
        """
        Execute create agent use case.

        Args:
            dto: CreateAgentDTO with agent details

        Returns:
            AgentCreatedResultDTO with created agent info

        Raises:
            ValueError: If agent data is invalid
            Exception: If persistence fails
        """
        try:
            logger.info(f"Creating agent {dto.agent_id} for tenant {dto.tenant_id}")

            # Step 1: Validate and build value objects
            agent_id = AgentId(dto.agent_id)

            # Build capabilities
            capabilities = []
            if dto.capabilities:
                for cap_dict in dto.capabilities:
                    cap = AgentCapability(
                        name=cap_dict["name"],
                        proficiency_level=cap_dict.get("level", 1),
                    )
                    capabilities.append(cap)
            else:
                raise ValueError("Agent must have at least one capability")

            # Build resource requirements
            if dto.resource_requirements:
                resource_req = ResourceRequirement(**dto.resource_requirements)
            else:
                resource_req = ResourceRequirement()

            # Step 2: Create domain aggregate (validates invariants)
            agent = AgentAggregate(
                agent_id=agent_id,
                tenant_id=dto.tenant_id,
                name=dto.name,
                agent_type=dto.agent_type,
                description=dto.description,
                capabilities=capabilities,
                resource_requirements=resource_req,
                metadata=dto.metadata or {},
                tags=set(dto.tags or []),
            )

            # Step 3: Save to repository
            await self.agent_repo.save(agent)
            logger.info(f"Agent {agent_id} saved to repository")

            # Step 4: Publish domain event
            event = AgentCreatedEvent(
                aggregate_id=agent_id.value,
                tenant_id=dto.tenant_id,
                name=agent.name,
                agent_type=agent.agent_type,
                capabilities=[c.name for c in capabilities],
                metadata=agent.metadata,
            )
            wrapper_event = AgentCreatedCQRSWrapperEvent(event)
            await self.event_bus.publish([wrapper_event])
            logger.info(f"Published AgentCreatedEvent for {agent_id}")

            # Step 5: Return result DTO
            result = AgentCreatedResultDTO(
                agent_id=agent_id.value,
                tenant_id=dto.tenant_id,
                name=agent.name,
                status=agent.status,
                created_at=agent.created_at,
                capabilities_count=len(capabilities),
            )

            logger.info(f"Successfully created agent {agent_id}: {result}")
            return result

        except ValueError as e:
            logger.error(f"Invalid agent data: {e}")
            raise ValueError(f"Failed to create agent: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error creating agent: {e}")
            raise Exception(f"Failed to create agent due to system error: {e}") from e
