from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict


@dataclass
class Event:
    event_id: str
    created_at: datetime


@dataclass
class TaskAssigned(Event):
    task_id: str
    agent_id: str
    task_details: Dict[str, Any]
