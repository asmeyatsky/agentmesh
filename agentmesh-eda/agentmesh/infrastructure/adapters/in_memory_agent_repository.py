"""
In-Memory Agent Repository Adapter

Architectural Intent:
- Provides a lightweight, non-persistent implementation of AgentRepositoryPort
- Used for development, testing, and API prototyping
- Thread-safe via dict-based storage with tenant isolation
"""

from typing import Optional, List, Dict
from agentmesh.domain.entities.agent_aggregate import AgentAggregate
from agentmesh.domain.ports.agent_repository_port import AgentRepositoryPort


class InMemoryAgentRepository(AgentRepositoryPort):
    """
    In-memory implementation of AgentRepositoryPort.

    Stores agents in a dict keyed by (tenant_id, agent_id).
    """

    def __init__(self):
        self._store: Dict[str, AgentAggregate] = {}

    def _key(self, agent_id: str, tenant_id: str) -> str:
        return f"{tenant_id}:{agent_id}"

    async def save(self, agent: AgentAggregate) -> None:
        key = self._key(agent.agent_id.value, agent.tenant_id)
        self._store[key] = agent

    async def get_by_id(self, agent_id: str, tenant_id: str) -> Optional[AgentAggregate]:
        return self._store.get(self._key(agent_id, tenant_id))

    async def find_by_capabilities(
        self,
        capabilities: List[str],
        tenant_id: str,
        match_all: bool = False,
    ) -> List[AgentAggregate]:
        results = []
        cap_set = set(capabilities)
        for agent in self._store.values():
            if agent.tenant_id != tenant_id:
                continue
            agent_caps = {c.name for c in agent.capabilities}
            if match_all and cap_set.issubset(agent_caps):
                results.append(agent)
            elif not match_all and cap_set & agent_caps:
                results.append(agent)
        return results

    async def find_all(self, tenant_id: str) -> List[AgentAggregate]:
        return [a for a in self._store.values() if a.tenant_id == tenant_id]

    async def find_available(self, tenant_id: str) -> List[AgentAggregate]:
        return [
            a
            for a in self._store.values()
            if a.tenant_id == tenant_id and a.status == "AVAILABLE"
        ]

    async def find_by_status(self, status: str, tenant_id: str) -> List[AgentAggregate]:
        return [
            a
            for a in self._store.values()
            if a.tenant_id == tenant_id and a.status == status
        ]

    async def delete(self, agent_id: str, tenant_id: str) -> bool:
        key = self._key(agent_id, tenant_id)
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def count(self, tenant_id: str) -> int:
        return sum(1 for a in self._store.values() if a.tenant_id == tenant_id)
