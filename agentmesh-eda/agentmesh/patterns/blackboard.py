from agentmesh.mal.router import MessageRouter
from agentmesh.mal.message import UniversalMessage
from loguru import logger


class Blackboard:
    def __init__(self, router: MessageRouter):
        self.router = router

    async def publish_update(self, domain: str, update_data: dict):
        logger.info(f"Publishing blackboard update for domain {domain}")
        message = UniversalMessage(
            payload=update_data,
            routing={"targets": [f"nats:blackboard.updates.{domain}"]},
        )
        await self.router.route_message(message)

    async def query_knowledge(self, agent_id: str, query_data: dict):
        logger.info(f"Agent {agent_id} querying blackboard knowledge")
        message = UniversalMessage(
            payload=query_data,
            routing={"targets": [f"nats:blackboard.queries.{agent_id}"]},
        )
        await self.router.route_message(message)
