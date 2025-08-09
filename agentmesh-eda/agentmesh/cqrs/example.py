from dataclasses import dataclass
from datetime import datetime
import uuid
from agentmesh.cqrs.command import Command
from agentmesh.cqrs.event import Event
from agentmesh.cqrs.handler import CommandHandler, EventHandler
from agentmesh.cqrs.event_store import InMemoryEventStore
from agentmesh.cqrs.bus import CommandBus
from agentmesh.utils.logging_config import setup_logging


# 1. Define Commands
@dataclass
class CreateAccount(Command):
    account_id: str
    initial_balance: float


@dataclass
class CreditAccount(Command):
    account_id: str
    amount: float


# 2. Define Events
@dataclass
class AccountCreated(Event):
    account_id: str
    initial_balance: float


@dataclass
class AccountCredited(Event):
    account_id: str
    amount: float


# 3. Define Aggregate
class BankAccount:
    def __init__(self, account_id: str):
        self.account_id = account_id
        self.balance = 0.0
        self.changes: list[Event] = []

    def create(self, initial_balance: float):
        event = AccountCreated(
            event_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            account_id=self.account_id,
            initial_balance=initial_balance,
        )
        self._apply(event)
        self.changes.append(event)

    def credit(self, amount: float):
        event = AccountCredited(
            event_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            account_id=self.account_id,
            amount=amount,
        )
        self._apply(event)
        self.changes.append(event)

    def _apply(self, event: Event):
        if isinstance(event, AccountCreated):
            self.balance = event.initial_balance
        elif isinstance(event, AccountCredited):
            self.balance += event.amount

    def load_from_history(self, events: list[Event]):
        for event in events:
            self._apply(event)


# 4. Define Command Handler
class BankAccountCommandHandler(CommandHandler):
    def __init__(self, event_store: InMemoryEventStore):
        self.event_store = event_store

    def handle(self, command: Command):
        if isinstance(command, CreateAccount):
            account = BankAccount(command.account_id)
            account.create(command.initial_balance)
            self.event_store.save_events(account.account_id, account.changes)
        elif isinstance(command, CreditAccount):
            events = self.event_store.load_events(command.account_id)
            account = BankAccount(command.account_id)
            account.load_from_history(events)
            account.credit(command.amount)
            self.event_store.save_events(account.account_id, account.changes)


# 5. Define Read Model and Event Handler
class BankAccountReadModel:
    def __init__(self):
        self.accounts: dict[str, float] = {}


class BankAccountEventHandler(EventHandler):
    def __init__(self, read_model: BankAccountReadModel):
        self.read_model = read_model

    def handle(self, event: Event):
        if isinstance(event, AccountCreated):
            self.read_model.accounts[event.account_id] = event.initial_balance
        elif isinstance(event, AccountCredited):
            self.read_model.accounts[event.account_id] += event.amount


def main():
    setup_logging()
    # Setup
    event_store = InMemoryEventStore()
    command_bus = CommandBus()

    command_handler = BankAccountCommandHandler(event_store)
    command_bus.register_handler(CreateAccount, command_handler)
    command_bus.register_handler(CreditAccount, command_handler)

    # Execute commands
    account_id = "123"
    command_bus.dispatch(CreateAccount(account_id=account_id, initial_balance=100.0))
    command_bus.dispatch(CreditAccount(account_id=account_id, amount=50.0))

    # Verify event store
    events = event_store.load_events(account_id)
    print(f"Events: {events}")

    # Verify read model
    read_model = BankAccountReadModel()
    event_handler = BankAccountEventHandler(read_model)
    for event in events:
        event_handler.handle(event)
    print(f"Read model: {read_model.accounts}")


if __name__ == "__main__":
    main()
