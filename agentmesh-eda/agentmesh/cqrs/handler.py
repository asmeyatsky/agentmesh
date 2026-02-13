from typing import Protocol
from agentmesh.cqrs.event import Event
from agentmesh.cqrs.command import Command
from agentmesh.cqrs.query import Query


class EventHandler(Protocol):
    def handle(self, event: Event): ...


class CommandHandler(Protocol):
    def handle(self, command: Command): ...


class QueryHandler(Protocol):
    def handle(self, query: Query): ...
