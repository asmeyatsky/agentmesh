"""
Tenant Repository Port

Architectural Intent:
- Defines interface for tenant data access
- Separates domain rules from database implementation
- Enables tenant isolation and multi-tenancy
- Supports tenant configuration and validation

Key Design Decisions:
1. Port defines repository pattern for tenant access
2. Immutable tenant value objects
3. Validation rules in domain layer
4. Caching friendly interface for performance
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from agentmesh.security.roles import UserRole


@dataclass(frozen=True)
class Tenant:
    """
    Immutable Tenant Value Object

    Invariants:
    - tenant_id must be non-empty string
    - name must be non-empty string
    - is_active must be boolean
    """
    tenant_id: str
    name: str
    api_key: str
    is_active: bool = True
    max_agents: int = 100
    max_messages_per_hour: int = 10000
    features: dict = None

    def __post_init__(self):
        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError("tenant_id cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("name cannot be empty")
        if not self.api_key or not self.api_key.strip():
            raise ValueError("api_key cannot be empty")


class TenantRepositoryPort(ABC):
    """
    Port: Access tenant information for routing and configuration.

    Responsibilities:
    - Retrieve tenant by ID
    - Validate tenant API keys
    - Check tenant status (active/suspended)
    - Retrieve tenant configuration
    """

    @abstractmethod
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """
        Get tenant by ID.

        Args:
            tenant_id: Unique tenant identifier

        Returns:
            Tenant if found and active, None otherwise

        Raises:
            Exception: If database access fails
        """
        pass

    @abstractmethod
    async def get_tenant_by_api_key(self, api_key: str) -> Optional[Tenant]:
        """
        Get tenant by API key (for authentication).

        Args:
            api_key: Tenant API key for authentication

        Returns:
            Tenant if found and active, None otherwise

        Raises:
            Exception: If database access fails
        """
        pass

    @abstractmethod
    async def is_tenant_active(self, tenant_id: str) -> bool:
        """
        Check if tenant is active (not suspended/deleted).

        Args:
            tenant_id: Tenant to check

        Returns:
            True if tenant is active, False otherwise

        Raises:
            Exception: If database access fails
        """
        pass

    @abstractmethod
    async def get_tenant_message_limit(self, tenant_id: str) -> int:
        """
        Get hourly message rate limit for tenant.

        Args:
            tenant_id: Tenant to check

        Returns:
            Maximum messages allowed per hour

        Raises:
            Exception: If database access fails
        """
        pass
