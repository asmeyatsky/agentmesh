import pytest
from unittest.mock import AsyncMock
from agentmesh.patterns.hierarchical import HierarchicalAgent
from agentmesh.mal.message import UniversalMessage


@pytest.fixture
def mock_coordinator():
    return AsyncMock()


@pytest.fixture
def mock_router():
    return AsyncMock()


@pytest.mark.asyncio
async def test_hierarchical_agent_send_upward_event(mock_coordinator, mock_router):
    agent = HierarchicalAgent(
        agent_id="agent1",
        level="tactical",
        coordinator=mock_coordinator,
        router=mock_router,
        tenant_id="test_tenant",
    )
    event_data = {"data": "some_event"}
    await agent.send_upward_event(event_data)

    mock_router.route_message.assert_called_once()
    args, kwargs = mock_router.route_message.call_args
    message = args[0]
    assert isinstance(message, UniversalMessage)
    assert message.payload == event_data
    assert message.routing["targets"] == ["nats:hierarchy.up.tactical.agent1"]
    assert message.tenant_id == "test_tenant"


@pytest.mark.asyncio
async def test_hierarchical_agent_send_downward_command(mock_coordinator, mock_router):
    agent = HierarchicalAgent(
        agent_id="agent1",
        level="strategic",
        coordinator=mock_coordinator,
        router=mock_router,
        tenant_id="test_tenant",
    )
    command_data = {"command": "do_something"}
    await agent.send_downward_command(
        target_agent_id="agent2", command_data=command_data
    )

    mock_router.route_message.assert_called_once()
    args, kwargs = mock_router.route_message.call_args
    message = args[0]
    assert isinstance(message, UniversalMessage)
    assert message.payload == command_data
    assert message.routing["targets"] == ["nats:hierarchy.down.strategic.agent2"]
    assert message.tenant_id == "test_tenant"


@pytest.mark.asyncio
async def test_hierarchical_agent_send_lateral_coordination(
    mock_coordinator, mock_router
):
    agent = HierarchicalAgent(
        agent_id="agent1",
        level="operational",
        coordinator=mock_coordinator,
        router=mock_router,
        tenant_id="test_tenant",
    )
    coordination_data = {"coord": "sync_data"}
    await agent.send_lateral_coordination(coordination_data)

    mock_router.route_message.assert_called_once()
    args, kwargs = mock_router.route_message.call_args
    message = args[0]
    assert isinstance(message, UniversalMessage)
    assert message.payload == coordination_data
    assert message.routing["targets"] == ["nats:hierarchy.lateral.operational"]
    assert message.tenant_id == "test_tenant"
