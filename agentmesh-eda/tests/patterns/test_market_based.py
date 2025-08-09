import pytest
from unittest.mock import AsyncMock
from agentmesh.patterns.market_based import Marketplace
from agentmesh.mal.message import UniversalMessage


@pytest.fixture
def mock_router():
    return AsyncMock()


@pytest.mark.asyncio
async def test_marketplace_publish_bid_request(mock_router):
    marketplace = Marketplace(router=mock_router)
    request_data = {"resource": "CPU", "amount": 10}
    tenant_id = "test_tenant"
    resource_type = "compute"
    await marketplace.publish_bid_request(
        tenant_id=tenant_id, resource_type=resource_type, request_data=request_data
    )

    mock_router.route_message.assert_called_once()
    args, kwargs = mock_router.route_message.call_args
    message = args[0]
    assert isinstance(message, UniversalMessage)
    assert message.payload == request_data
    assert message.routing["targets"] == [
        f"nats:market.requests.{tenant_id}.{resource_type}"
    ]
    assert message.tenant_id == tenant_id


@pytest.mark.asyncio
async def test_marketplace_publish_bid_response(mock_router):
    marketplace = Marketplace(router=mock_router)
    response_data = {"bid": 10, "status": "accepted"}
    tenant_id = "test_tenant"
    bidder_id = "bidder1"
    await marketplace.publish_bid_response(
        tenant_id=tenant_id, bidder_id=bidder_id, response_data=response_data
    )

    mock_router.route_message.assert_called_once()
    args, kwargs = mock_router.route_message.call_args
    message = args[0]
    assert isinstance(message, UniversalMessage)
    assert message.payload == response_data
    assert message.routing["targets"] == [f"nats:market.responses.{tenant_id}.{bidder_id}"]
    assert message.tenant_id == tenant_id


@pytest.mark.asyncio
async def test_marketplace_publish_settlement(mock_router):
    marketplace = Marketplace(router=mock_router)
    settlement_data = {"transaction_id": "txn123", "amount": 100}
    tenant_id = "test_tenant"
    transaction_id = "txn123"
    await marketplace.publish_settlement(
        tenant_id=tenant_id,
        transaction_id=transaction_id,
        settlement_data=settlement_data,
    )

    mock_router.route_message.assert_called_once()
    args, kwargs = mock_router.route_message.call_args
    message = args[0]
    assert isinstance(message, UniversalMessage)
    assert message.payload == settlement_data
    assert message.routing["targets"] == [
        f"nats:market.settlements.{tenant_id}.{transaction_id}"
    ]
    assert message.tenant_id == tenant_id
