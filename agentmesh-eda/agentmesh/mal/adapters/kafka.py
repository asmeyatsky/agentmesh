from agentmesh.mal.adapters.base import MessagePlatformAdapter
from agentmesh.mal.message import UniversalMessage
from confluent_kafka import Producer, Consumer
import asyncio


class KafkaAdapter(MessagePlatformAdapter):
    def __init__(self, bootstrap_servers: str):
        self.producer = Producer({"bootstrap.servers": bootstrap_servers})
        self.consumer_config = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": "agentmesh",
            "auto.offset.reset": "earliest",
        }

    async def send(self, message: UniversalMessage, target: str):
        self.producer.produce(target, message.serialize())
        self.producer.flush()

    async def consume(self, subscription: str):
        consumer = Consumer(self.consumer_config)
        consumer.subscribe([subscription])
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                await asyncio.sleep(0.1)
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue
            yield UniversalMessage.deserialize(msg.value())
