from agentmesh.mal.adapters.base import MessagePlatformAdapter
from agentmesh.mal.message import UniversalMessage
from google.cloud import pubsub_v1
import asyncio


class PubSubAdapter(MessagePlatformAdapter):
    def __init__(self, project_id: str):
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()
        self.project_id = project_id

    async def send(self, message: UniversalMessage, target: str):
        topic_path = self.publisher.topic_path(self.project_id, target)
        future = self.publisher.publish(topic_path, message.serialize())
        future.result()

    async def consume(self, subscription_name: str):
        subscription_path = self.subscriber.subscription_path(
            self.project_id, subscription_name
        )
        queue = asyncio.Queue()

        def callback(message: pubsub_v1.subscriber.message.Message) -> None:
            queue.put_nowait(message)
            message.ack()

        self.subscriber.subscribe(
            subscription_path, callback=callback
        )

        with self.subscriber:
            while True:
                message = await queue.get()
                yield UniversalMessage.deserialize(message.data)
