from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Dict, Any
from agentmesh.cqrs.query import Query, GetAgentStatusQuery
from loguru import logger

# Define a type variable for queries
Q = TypeVar('Q', bound=Query)

class QueryHandler(ABC, Generic[Q]):
    """Base class for all query handlers."""

    @abstractmethod
    async def handle(self, query: Q) -> Any:
        pass


class GetAgentStatusQueryHandler(QueryHandler[GetAgentStatusQuery]):
    def __init__(self, agent_status_read_model: Dict[str, Any]):
        self.agent_status_read_model = agent_status_read_model

    async def handle(self, query: GetAgentStatusQuery) -> Dict[str, Any]:
        logger.info(f"Handling GetAgentStatusQuery for agent {query.agent_id} in tenant {query.tenant_id}")
        # In a real system, this would query a dedicated read model/database
        agent_key = f"{query.tenant_id}:{query.agent_id}"
        status = self.agent_status_read_model.get(agent_key, {"status": "unknown", "last_update": None})
        return {"agent_id": query.agent_id, "tenant_id": query.tenant_id, "status": status}