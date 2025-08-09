from agentmesh.mal.router import MessageRouter
from agentmesh.mal.message import UniversalMessage
from loguru import logger


class Marketplace:
    def __init__(self, router: MessageRouter):
        self.router = router

    async def publish_bid_request(self, resource_type: str, request_data: dict):
        logger.info(f"Publishing bid request for resource type: {resource_type}")
        message = UniversalMessage(
            payload=request_data,
            routing={"targets": [f"nats:market.requests.{resource_type}"]},
        )
        await self.router.route_message(message)

    async def publish_bid_response(self, bidder_id: str, response_data: dict):
        logger.info(f"Publishing bid response from bidder: {bidder_id}")
        message = UniversalMessage(
            payload=response_data,
            routing={"targets": [f"nats:market.responses.{bidder_id}"]},
        )
        await self.router.route_message(message)

    async def publish_settlement(self, transaction_id: str, settlement_data: dict):
        logger.info(f"Publishing settlement for transaction: {transaction_id}")
        message = UniversalMessage(
            payload=settlement_data,
            routing={"targets": [f"nats:market.settlements.{transaction_id}"]},
        )
        await self.router.route_message(message)
