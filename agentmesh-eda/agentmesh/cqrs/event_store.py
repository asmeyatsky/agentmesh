from typing import List, Protocol
from agentmesh.cqrs.event import Event
from agentmesh.utils.metrics import EVENT_STORE_EVENTS_SAVED


class EventStore(Protocol):
    def save_events(self, aggregate_id: str, events: List[Event]): ...

    def load_events(self, aggregate_id: str) -> List[Event]: ...


class InMemoryEventStore(EventStore):
    def __init__(self):
        self.events: dict[str, List[Event]] = {}

    def save_events(self, aggregate_id: str, events: List[Event]):
        if aggregate_id not in self.events:
            self.events[aggregate_id] = []
        self.events[aggregate_id].extend(events)
        for event in events:
            EVENT_STORE_EVENTS_SAVED.labels(
                aggregate_id=aggregate_id, event_type=type(event).__name__
            ).inc()

    def load_events(self, aggregate_id: str) -> List[Event]:
        return self.events.get(aggregate_id, [])
