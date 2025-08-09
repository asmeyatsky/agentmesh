from typing import Protocol
from agentmesh.cqrs.event import Event
from agentmesh.cqrs.command import Command


class EventHandler(Protocol):
    def handle(self, event: Event): ...


class CommandHandler(Protocol):
    def handle(self, command: Command): ...
