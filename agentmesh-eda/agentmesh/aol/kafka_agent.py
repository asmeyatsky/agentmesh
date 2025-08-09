from loguru import logger
from agentmesh.aol.simple_agent import SimpleAgent
from agentmesh.mal.message import UniversalMessage
from agentmesh.mal.adapters.base import MessagePlatformAdapter


class KafkaAgent(SimpleAgent):
    def __init__(
        self, id: str, capabilities: list[str], adapter: MessagePlatformAdapter
    ):
        super().__init__(id, capabilities, adapter)
        self.subscription_topic = f"agent.kafka_agent.{self.id}.commands"

    async def process_message(self, message: UniversalMessage):
        logger.info(f"KafkaAgent {self.id} received message: {message.payload}")
        # Here, the Kafka agent would process the message
