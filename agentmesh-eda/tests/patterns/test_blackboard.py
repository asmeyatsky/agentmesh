import pytest
from unittest.mock import AsyncMock
from agentmesh.patterns.blackboard import Blackboard
from agentmesh.mal.message import UniversalMessage


@pytest.fixture
def mock_router():
    return AsyncMock()


@pytest.mark.asyncio
async def test_blackboard_publish_update(mock_router):
    blackboard = Blackboard(router=mock_router)
    update_data = {"key": "value"}
    await blackboard.publish_update(domain="test_domain", update_data=update_data)

    mock_router.route_message.assert_called_once()
    args, kwargs = mock_router.route_message.call_args
    message = args[0]
    assert isinstance(message, UniversalMessage)
    assert message.payload == update_data
    assert message.routing["targets"] == ["nats:blackboard.updates.test_domain"]
    assert (
        message.tenant_id == "default_tenant"
    )  # Default tenant for blackboard messages


@pytest.mark.asyncio
async def test_blackboard_query_knowledge(mock_router):
    blackboard = Blackboard(router=mock_router)
    query_data = {"query": "what is x?"}
    await blackboard.query_knowledge(agent_id="agent1", query_data=query_data)

    mock_router.route_message.assert_called_once()
    args, kwargs = mock_router.route_message.call_args
    message = args[0]
    assert isinstance(message, UniversalMessage)
    assert message.payload == query_data
    assert message.routing["targets"] == ["nats:blackboard.queries.agent1"]
    assert (
        message.tenant_id == "default_tenant"
    )  # Default tenant for blackboard messages
