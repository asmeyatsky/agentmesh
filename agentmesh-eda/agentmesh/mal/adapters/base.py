from abc import ABC, abstractmethod
from agentmesh.mal.message import UniversalMessage


class MessagePlatformAdapter(ABC):
    @abstractmethod
    async def send(self, message: UniversalMessage, target: str):
        pass

    @abstractmethod
    async def consume(self, subscription: str):
        pass
