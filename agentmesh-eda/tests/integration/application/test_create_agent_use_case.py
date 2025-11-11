"""
Integration Tests: CreateAgentUseCase

Tests the full flow from input DTO through domain logic to persistence.

Architectural Intent:
- Verify use case orchestrates domain correctly
- Verify events are published
- Verify persistence works
- Verify tenant isolation
"""

import pytest
from datetime import datetime

from agentmesh.application.use_cases.create_agent_use_case import CreateAgentUseCase, CreateAgentDTO
from agentmesh.domain.value_objects.agent_value_objects import AgentCapability
from agentmesh.cqrs.bus import EventBus
from agentmesh.domain.domain_events.agent_events import AgentCreatedEvent


class InMemoryAgentRepository:
    """Mock repository for testing"""
    def __init__(self):
        self.agents = {}

    async def save(self, agent):
        self.agents[agent.agent_id.value] = agent

    async def get_by_id(self, agent_id, tenant_id):
        return self.agents.get(agent_id)


class InMemoryEventBus:
    """Mock event bus for testing"""
    def __init__(self):
        self.events = []

    async def publish(self, event):
        self.events.append(event)


@pytest.mark.asyncio
class TestCreateAgentUseCase:
    """Integration tests for agent creation"""

    @pytest.fixture
    def setup(self):
        """Setup use case with mock dependencies"""
        repository = InMemoryAgentRepository()
        event_bus = InMemoryEventBus()
        use_case = CreateAgentUseCase(repository, event_bus)
        return use_case, repository, event_bus

    async def test_create_agent_successfully(self, setup):
        """Happy path: Create agent with valid data"""
        use_case, repo, bus = setup

        dto = CreateAgentDTO(
            tenant_id="tenant-1",
            agent_id="agent-001",
            name="Data Processor",
            agent_type="processor",
            description="Processes incoming data",
            capabilities=[
                {"name": "data_processing", "level": 4},
                {"name": "analysis", "level": 3}
            ],
            metadata={"version": "1.0"},
            tags=["production", "critical"]
        )

        result = await use_case.execute(dto)

        # Verify result
        assert result.agent_id == "agent-001"
        assert result.tenant_id == "tenant-1"
        assert result.name == "Data Processor"
        assert result.capabilities_count == 2
        assert result.status == "AVAILABLE"

    async def test_agent_persisted_to_repository(self, setup):
        """Verify agent is saved to repository"""
        use_case, repo, bus = setup

        dto = CreateAgentDTO(
            tenant_id="tenant-1",
            agent_id="agent-002",
            name="Analyzer",
            capabilities=[{"name": "analysis", "level": 5}]
        )

        await use_case.execute(dto)

        # Verify in repository
        saved_agent = await repo.get_by_id("agent-002", "tenant-1")
        assert saved_agent is not None
        assert saved_agent.name == "Analyzer"
        assert len(saved_agent.capabilities) == 1
        assert saved_agent.capabilities[0].name == "analysis"

    async def test_domain_event_published(self, setup):
        """Verify AgentCreatedEvent is published"""
        use_case, repo, bus = setup

        dto = CreateAgentDTO(
            tenant_id="tenant-1",
            agent_id="agent-003",
            name="Event Test Agent",
            capabilities=[{"name": "test", "level": 2}]
        )

        await use_case.execute(dto)

        # Verify event published
        assert len(bus.events) == 1
        event = bus.events[0]
        assert isinstance(event, AgentCreatedEvent)
        assert event.agent_id == "agent-003"
        assert event.tenant_id == "tenant-1"
        assert event.name == "Event Test Agent"

    async def test_multiple_agents_created(self, setup):
        """Verify multiple agents can be created independently"""
        use_case, repo, bus = setup

        agent1_dto = CreateAgentDTO(
            tenant_id="tenant-1",
            agent_id="agent-a",
            name="Agent A",
            capabilities=[{"name": "task_a", "level": 3}]
        )

        agent2_dto = CreateAgentDTO(
            tenant_id="tenant-1",
            agent_id="agent-b",
            name="Agent B",
            capabilities=[{"name": "task_b", "level": 4}]
        )

        result1 = await use_case.execute(agent1_dto)
        result2 = await use_case.execute(agent2_dto)

        assert result1.agent_id == "agent-a"
        assert result2.agent_id == "agent-b"

        # Verify both in repository
        saved1 = await repo.get_by_id("agent-a", "tenant-1")
        saved2 = await repo.get_by_id("agent-b", "tenant-1")
        assert saved1 is not None
        assert saved2 is not None

    async def test_tenant_isolation(self, setup):
        """Verify agents are isolated by tenant"""
        use_case, repo, bus = setup

        agent1_dto = CreateAgentDTO(
            tenant_id="tenant-1",
            agent_id="shared-id",
            name="Agent in Tenant 1",
            capabilities=[{"name": "test", "level": 1}]
        )

        agent2_dto = CreateAgentDTO(
            tenant_id="tenant-2",
            agent_id="shared-id",
            name="Agent in Tenant 2",
            capabilities=[{"name": "test", "level": 1}]
        )

        result1 = await use_case.execute(agent1_dto)
        result2 = await use_case.execute(agent2_dto)

        # Both should exist but be isolated
        assert result1.tenant_id == "tenant-1"
        assert result2.tenant_id == "tenant-2"

        # Verify tenant isolation in repository
        agent1 = await repo.get_by_id("shared-id", "tenant-1")
        agent2 = await repo.get_by_id("shared-id", "tenant-2")
        assert agent1.name == "Agent in Tenant 1"
        assert agent2.name == "Agent in Tenant 2"

    async def test_invalid_agent_data_rejected(self, setup):
        """Verify invalid agent data is rejected"""
        use_case, repo, bus = setup

        invalid_dto = CreateAgentDTO(
            tenant_id="tenant-1",
            agent_id="invalid",
            name="Invalid Agent",
            capabilities=[]  # INVALID: No capabilities
        )

        with pytest.raises(ValueError):
            await use_case.execute(invalid_dto)

    async def test_agent_created_with_full_metadata(self, setup):
        """Verify agent preserves all metadata"""
        use_case, repo, bus = setup

        dto = CreateAgentDTO(
            tenant_id="tenant-1",
            agent_id="full-metadata",
            name="Full Metadata Agent",
            agent_type="custom_type",
            description="Test with full metadata",
            capabilities=[
                {"name": "skill1", "level": 1},
                {"name": "skill2", "level": 2},
                {"name": "skill3", "level": 3}
            ],
            metadata={"key1": "value1", "key2": "value2"},
            tags=["tag1", "tag2", "tag3"]
        )

        result = await use_case.execute(dto)
        assert result.capabilities_count == 3

        # Verify all metadata saved
        saved = await repo.get_by_id("full-metadata", "tenant-1")
        assert saved.agent_type == "custom_type"
        assert saved.description == "Test with full metadata"
        assert saved.metadata == {"key1": "value1", "key2": "value2"}
        assert len(saved.tags) == 3
