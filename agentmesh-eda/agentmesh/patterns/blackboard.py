from agentmesh.mal.router import MessageRouter
from agentmesh.mal.message import UniversalMessage
from loguru import logger


class Blackboard:
    def __init__(self, router: MessageRouter):
        self.router = router

    async def publish_update(self, tenant_id: str, domain: str, update_data: dict):
        logger.info(f"Publishing blackboard update for tenant {tenant_id}, domain {domain}")
        message = UniversalMessage(
            tenant_id=tenant_id,
            payload=update_data,
            routing={"targets": [f"nats:blackboard.updates.{tenant_id}.{domain}"]},
        )
        await self.router.route_message(message)

    async def query_knowledge(self, tenant_id: str, agent_id: str, query_data: dict):
        logger.info(f"Agent {agent_id} querying blackboard knowledge for tenant {tenant_id}")
        message = UniversalMessage(
            tenant_id=tenant_id,
            payload=query_data,
            routing={"targets": [f"nats:blackboard.queries.{tenant_id}.{agent_id}"]},
        )
        await self.router.route_message(message)
