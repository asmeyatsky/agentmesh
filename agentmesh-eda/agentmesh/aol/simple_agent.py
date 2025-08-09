from loguru import logger
from agentmesh.aol.agent import Agent
from agentmesh.mal.message import UniversalMessage
from agentmesh.mal.adapters.base import MessagePlatformAdapter


class SimpleAgent(Agent):
    def __init__(
        self, id: str, capabilities: list[str], adapter: MessagePlatformAdapter
    ):
        super().__init__(id, capabilities)
        self.adapter = adapter
        self.subscription_topic = f"agent.{self.id}.commands"

    async def start(self):
        logger.info(f"SimpleAgent {self.id} starting and subscribing to {self.subscription_topic}")
        await self.adapter.consume(self.subscription_topic, self.process_message)

    async def process_message(self, message: UniversalMessage):
        logger.info(f"SimpleAgent {self.id} received message: {message.payload}")
        # Here, the agent would process the message based on its capabilities
        # For this example, we just log the message.
