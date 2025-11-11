"""
Agent Repository Port

Architectural Intent:
- Defines interface for agent persistence
- Separates domain logic from storage implementation
- Enables multiple storage backends (PostgreSQL, MongoDB, etc.)
- Supports agent discovery and querying

Key Design Decisions:
1. Port interface in domain layer (not infrastructure)
2. Returns domain aggregates, not ORM models
3. Supports filtering by capabilities and tenant
4. Includes consistency guarantees
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from agentmesh.domain.entities.agent_aggregate import AgentAggregate


class AgentRepositoryPort(ABC):
    """
    Port: Persist and retrieve agent aggregates.

    Responsibilities:
    - Save agent aggregates
    - Retrieve by ID (with tenant isolation)
    - Find by capabilities
    - List all agents per tenant
    - Delete agents
    """

    @abstractmethod
    async def save(self, agent: AgentAggregate) -> None:
        """
        Save (create or update) agent aggregate.

        Args:
            agent: AgentAggregate to persist

        Raises:
            Exception: If save fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, agent_id: str, tenant_id: str) -> Optional[AgentAggregate]:
        """
        Get agent by ID (with tenant isolation).

        Args:
            agent_id: Agent ID to retrieve
            tenant_id: Tenant ID for isolation

        Returns:
            AgentAggregate if found, None otherwise

        Raises:
            Exception: If query fails
        """
        pass

    @abstractmethod
    async def find_by_capabilities(self,
                                   capabilities: List[str],
                                   tenant_id: str,
                                   match_all: bool = False) -> List[AgentAggregate]:
        """
        Find agents with specific capabilities.

        Args:
            capabilities: List of capability names to search for
            tenant_id: Tenant ID for isolation
            match_all: If True, agent must have ALL capabilities.
                       If False, agent must have ANY capability.

        Returns:
            List of matching agents

        Raises:
            Exception: If query fails
        """
        pass

    @abstractmethod
    async def find_all(self, tenant_id: str) -> List[AgentAggregate]:
        """
        Get all agents for tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            List of all agents for tenant

        Raises:
            Exception: If query fails
        """
        pass

    @abstractmethod
    async def find_available(self, tenant_id: str) -> List[AgentAggregate]:
        """
        Get all available (not busy, not paused) agents.

        Args:
            tenant_id: Tenant ID

        Returns:
            List of agents with AVAILABLE status

        Raises:
            Exception: If query fails
        """
        pass

    @abstractmethod
    async def find_by_status(self, status: str, tenant_id: str) -> List[AgentAggregate]:
        """
        Find agents by status.

        Args:
            status: Status to filter by (AVAILABLE, BUSY, PAUSED, etc.)
            tenant_id: Tenant ID

        Returns:
            List of agents with matching status

        Raises:
            Exception: If query fails
        """
        pass

    @abstractmethod
    async def delete(self, agent_id: str, tenant_id: str) -> bool:
        """
        Delete agent.

        Args:
            agent_id: Agent to delete
            tenant_id: Tenant ID

        Returns:
            True if deleted, False if not found

        Raises:
            Exception: If delete fails
        """
        pass

    @abstractmethod
    async def count(self, tenant_id: str) -> int:
        """
        Count agents for tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            Number of agents

        Raises:
            Exception: If query fails
        """
        pass
