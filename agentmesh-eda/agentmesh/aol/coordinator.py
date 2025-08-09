from agentmesh.aol.registry import AgentRegistry
from agentmesh.mal.router import MessageRouter
from agentmesh.mal.message import UniversalMessage
from loguru import logger


class AgentCoordinator:
    def __init__(self, registry: AgentRegistry, router: MessageRouter):
        self.registry = registry
        self.router = router

    async def coordinate_task(
        self, task_requirements: dict, token: str = None, tenant_id: str = None
    ):
        agents = self.registry.discover_agents(task_requirements, tenant_id=tenant_id)
        if not agents:
            logger.warning("No agents found for the task")
            return

        # Simple coordination: assign task to the first available agent
        agent = agents[0]
        logger.info(f"Coordinating task for agent {agent.id}")
        message = UniversalMessage(
            payload={"task": task_requirements},
            routing={"targets": [f"nats:agent.{agent.id}.tasks"]},
            metadata={"token": token} if token else {},
            tenant_id=tenant_id if tenant_id else "default_tenant",  # Pass tenant_id
        )
        await self.router.route_message(message)
