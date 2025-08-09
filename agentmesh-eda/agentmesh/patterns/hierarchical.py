from agentmesh.aol.coordinator import AgentCoordinator
from agentmesh.mal.router import MessageRouter
from agentmesh.mal.message import UniversalMessage
from loguru import logger


class HierarchicalAgent:
    def __init__(
        self,
        agent_id: str,
        level: str,
        coordinator: AgentCoordinator,
        router: MessageRouter,
        tenant_id: str = "default_tenant",
    ):
        self.agent_id = agent_id
        self.level = level
        self.coordinator = coordinator
        self.router = router
        self.tenant_id = tenant_id

    async def send_upward_event(self, event_data: dict):
        logger.info(f"Agent {self.agent_id} sending upward event to level {self.level}")
        message = UniversalMessage(
            payload=event_data,
            routing={"targets": [f"nats:hierarchy.up.{self.level}.{self.agent_id}"]},
            tenant_id=self.tenant_id,
        )
        await self.router.route_message(message)

    async def send_downward_command(self, target_agent_id: str, command_data: dict):
        logger.info(
            f"Agent {self.agent_id} sending downward command to {target_agent_id}"
        )
        message = UniversalMessage(
            payload=command_data,
            routing={
                "targets": [f"nats:hierarchy.down.{self.level}.{target_agent_id}"]
            },
            tenant_id=self.tenant_id,
        )
        await self.router.route_message(message)

    async def send_lateral_coordination(self, coordination_data: dict):
        logger.info(
            f"Agent {self.agent_id} sending lateral coordination event at level {self.level}"
        )
        message = UniversalMessage(
            payload=coordination_data,
            routing={"targets": [f"nats:hierarchy.lateral.{self.level}"]},
            tenant_id=self.tenant_id,
        )
        await self.router.route_message(message)
