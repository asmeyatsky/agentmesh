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
    tenant_id = "test_tenant"
    await blackboard.publish_update(
        tenant_id=tenant_id, domain="test_domain", update_data=update_data
    )

    mock_router.route_message.assert_called_once()
    args, kwargs = mock_router.route_message.call_args
    message = args[0]
    assert isinstance(message, UniversalMessage)
    assert message.payload == update_data
    assert message.routing["targets"] == [
        f"nats:blackboard.updates.{tenant_id}.test_domain"
    ]
    assert message.tenant_id == tenant_id


@pytest.mark.asyncio
async def test_blackboard_query_knowledge(mock_router):
    blackboard = Blackboard(router=mock_router)
    query_data = {"query": "what is x?"}
    tenant_id = "test_tenant"
    agent_id = "agent1"
    await blackboard.query_knowledge(
        tenant_id=tenant_id, agent_id=agent_id, query_data=query_data
    )

    mock_router.route_message.assert_called_once()
    args, kwargs = mock_router.route_message.call_args
    message = args[0]
    assert isinstance(message, UniversalMessage)
    assert message.payload == query_data
    assert message.routing["targets"] == [
        f"nats:blackboard.queries.{tenant_id}.{agent_id}"
    ]
    assert message.tenant_id == tenant_id
