import pytest
import asyncio
from agentmesh.aol.coordinator import AgentCoordinator
from agentmesh.aol.registry import AgentRegistry
from agentmesh.aol.agent import Agent
from agentmesh.mal.router import MessageRouter
from agentmesh.mal.adapters.base import MessagePlatformAdapter
from agentmesh.mal.message import UniversalMessage


class MockAdapter(MessagePlatformAdapter):
    def __init__(self):
        self.sent_messages = []

    async def send(self, message: UniversalMessage, target: str):
        self.sent_messages.append((message, target))
        await asyncio.sleep(0)

    async def consume(self, subscription: str):
        pass


@pytest.mark.asyncio
async def test_agent_coordinator(valid_token):
    registry = AgentRegistry()
    agent = Agent(id="test_agent", capabilities=["test"], tenant_id="test_tenant")
    registry.register_agent(agent)

    router = MessageRouter()
    mock_adapter = MockAdapter()
    router.add_adapter("nats", mock_adapter)

    coordinator = AgentCoordinator(registry, router)
    await coordinator.coordinate_task(
        {"capability": "test"}, token=valid_token, tenant_id="test_tenant"
    )

    assert len(mock_adapter.sent_messages) == 1
    sent_message, target = mock_adapter.sent_messages[0]
    assert sent_message.tenant_id == "test_tenant"  # Assert tenant_id in message
    assert target == "agent.test_agent.tasks"
