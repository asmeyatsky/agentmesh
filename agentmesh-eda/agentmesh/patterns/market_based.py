from agentmesh.mal.router import MessageRouter
from agentmesh.mal.message import UniversalMessage
from loguru import logger


class Marketplace:
    def __init__(self, router: MessageRouter):
        self.router = router

    async def publish_bid_request(
        self, tenant_id: str, resource_type: str, request_data: dict
    ):
        logger.info(
            f"Publishing bid request for tenant {tenant_id}, resource type: {resource_type}"
        )
        message = UniversalMessage(
            tenant_id=tenant_id,
            payload=request_data,
            routing={"targets": [f"nats:market.requests.{tenant_id}.{resource_type}"]},
        )
        await self.router.route_message(message)

    async def publish_bid_response(
        self, tenant_id: str, bidder_id: str, response_data: dict
    ):
        logger.info(f"Publishing bid response from bidder: {bidder_id} for tenant {tenant_id}")
        message = UniversalMessage(
            tenant_id=tenant_id,
            payload=response_data,
            routing={"targets": [f"nats:market.responses.{tenant_id}.{bidder_id}"]},
        )
        await self.router.route_message(message)

    async def publish_settlement(
        self, tenant_id: str, transaction_id: str, settlement_data: dict
    ):
        logger.info(
            f"Publishing settlement for transaction: {transaction_id} for tenant {tenant_id}"
        )
        message = UniversalMessage(
            tenant_id=tenant_id,
            payload=settlement_data,
            routing={"targets": [f"nats:market.settlements.{tenant_id}.{transaction_id}"]},
        )
        await self.router.route_message(message)
