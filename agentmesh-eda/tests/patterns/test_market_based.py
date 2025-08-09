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
    await marketplace.publish_bid_request(
        resource_type="compute", request_data=request_data
    )

    mock_router.route_message.assert_called_once()
    args, kwargs = mock_router.route_message.call_args
    message = args[0]
    assert isinstance(message, UniversalMessage)
    assert message.payload == request_data
    assert message.routing["targets"] == ["nats:market.requests.compute"]
    assert message.tenant_id == "default_tenant"  # Default tenant for market messages


@pytest.mark.asyncio
async def test_marketplace_publish_bid_response(mock_router):
    marketplace = Marketplace(router=mock_router)
    response_data = {"bid": 10, "status": "accepted"}
    await marketplace.publish_bid_response(
        bidder_id="bidder1", response_data=response_data
    )

    mock_router.route_message.assert_called_once()
    args, kwargs = mock_router.route_message.call_args
    message = args[0]
    assert isinstance(message, UniversalMessage)
    assert message.payload == response_data
    assert message.routing["targets"] == ["nats:market.responses.bidder1"]
    assert message.tenant_id == "default_tenant"  # Default tenant for market messages


@pytest.mark.asyncio
async def test_marketplace_publish_settlement(mock_router):
    marketplace = Marketplace(router=mock_router)
    settlement_data = {"transaction_id": "txn123", "amount": 100}
    await marketplace.publish_settlement(
        transaction_id="txn123", settlement_data=settlement_data
    )

    mock_router.route_message.assert_called_once()
    args, kwargs = mock_router.route_message.call_args
    message = args[0]
    assert isinstance(message, UniversalMessage)
    assert message.payload == settlement_data
    assert message.routing["targets"] == ["nats:market.settlements.txn123"]
    assert message.tenant_id == "default_tenant"  # Default tenant for market messages
