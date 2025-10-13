from abc import ABC
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Query(ABC):
    """Base class for all queries."""
    pass


@dataclass
class GetAgentStatusQuery(Query):
    agent_id: str
    tenant_id: str