from agentmesh.mal.adapters.base import MessagePlatformAdapter
from agentmesh.mal.message import UniversalMessage
import pulsar


class PulsarAdapter(MessagePlatformAdapter):
    def __init__(self, service_url: str):
        self.client = pulsar.Client(service_url)

    async def send(self, message: UniversalMessage, target: str):
        producer = self.client.create_producer(target)
        producer.send(message.serialize())

    async def consume(self, subscription: str):
        consumer = self.client.subscribe(subscription, "agentmesh-subscription")
        while True:
            msg = consumer.receive()
            try:
                yield UniversalMessage.deserialize(msg.data())
                consumer.acknowledge(msg)
            except Exception:
                consumer.negative_acknowledge(msg)

    def close(self):
        self.client.close()
