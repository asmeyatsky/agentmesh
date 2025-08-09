from agentmesh.cqrs.event import Event
from agentmesh.cqrs.command import Command
from agentmesh.cqrs.handler import CommandHandler
from agentmesh.mal.router import MessageRouter
from agentmesh.mal.message import UniversalMessage
from typing import Dict, List, Type
from agentmesh.utils.metrics import COMMANDS_DISPATCHED


class EventBus:
    def __init__(self, router: MessageRouter):
        self.router = router

    async def publish(self, events: List[Event]):
        for event in events:
            message = UniversalMessage(
                payload=event.__dict__,
                routing={"targets": [f"nats:events.{type(event).__name__}"]},
            )
            await self.router.route_message(message)


class CommandBus:
    def __init__(self):
        self.handlers: Dict[Type[Command], CommandHandler] = {}

    def register_handler(self, command_type: Type[Command], handler: CommandHandler):
        self.handlers[command_type] = handler

    def dispatch(self, command: Command):
        handler = self.handlers.get(type(command))
        if handler:
            handler.handle(command)
            COMMANDS_DISPATCHED.labels(command_type=type(command).__name__).inc()
