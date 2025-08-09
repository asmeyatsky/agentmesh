from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    event_id: str
    created_at: datetime
