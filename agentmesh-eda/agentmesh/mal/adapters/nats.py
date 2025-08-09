from agentmesh.mal.adapters.base import MessagePlatformAdapter
from agentmesh.mal.message import UniversalMessage
import nats


class NATSAdapter(MessagePlatformAdapter):
    def __init__(self, servers: list[str]):
        self.servers = servers
        self.nc = None

    async def connect(self):
        self.nc = await nats.connect(self.servers)

    async def send(self, message: UniversalMessage, target: str):
        if not self.nc:
            await self.connect()
        await self.nc.publish(target, message.serialize())

    async def consume(self, subscription: str):
        if not self.nc:
            await self.connect()
        sub = await self.nc.subscribe(subscription)
        async for msg in sub.messages:
            yield UniversalMessage.deserialize(msg.data)

    async def close(self):
        if self.nc:
            await self.nc.close()
