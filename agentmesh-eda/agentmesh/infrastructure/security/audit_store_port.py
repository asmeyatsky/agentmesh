"""
Port interface for audit log storage.

Enables multiple backend implementations (PostgreSQL, DynamoDB, Elasticsearch, etc.)
for audit trail persistence with immutable append-only semantics.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class AuditLogQuery:
    """Query parameters for audit log retrieval"""
    tenant_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    actor_id: Optional[str] = None
    resource_type: Optional[str] = None
    action: Optional[str] = None
    status: Optional[str] = None
    limit: int = 1000
    offset: int = 0


class AuditStorePort(ABC):
    """
    Port for persistent audit log storage.

    Guarantees:
    - Immutable append-only semantics
    - Tamper-evident logging (hashing, signing)
    - Compliance with regulatory requirements
    - Query support with filtering and pagination
    """

    @abstractmethod
    async def append(self, entry: 'AuditLogEntry') -> str:
        """
        Append audit log entry (immutable write).

        Args:
            entry: Audit log entry to persist

        Returns:
            Entry ID for reference
        """
        pass

    @abstractmethod
    async def query(self, query: AuditLogQuery) -> List['AuditLogEntry']:
        """
        Query audit logs with filters.

        Args:
            query: Query parameters

        Returns:
            List of matching audit log entries
        """
        pass

    @abstractmethod
    async def get_by_id(self, entry_id: str) -> Optional['AuditLogEntry']:
        """Get single audit log entry by ID"""
        pass

    @abstractmethod
    async def get_by_request_id(self, request_id: str) -> List['AuditLogEntry']:
        """Get all audit entries for a request"""
        pass

    @abstractmethod
    async def get_actor_history(self,
                               tenant_id: str,
                               actor_id: str,
                               limit: int = 100) -> List['AuditLogEntry']:
        """Get recent activity for an actor"""
        pass

    @abstractmethod
    async def get_resource_history(self,
                                  tenant_id: str,
                                  resource_id: str,
                                  limit: int = 100) -> List['AuditLogEntry']:
        """Get audit trail for a resource"""
        pass

    @abstractmethod
    async def export_range(self,
                          tenant_id: str,
                          start_date: datetime,
                          end_date: datetime) -> bytes:
        """Export audit logs for compliance/archival (e.g., as JSON or CSV)"""
        pass

    @abstractmethod
    async def verify_integrity(self) -> bool:
        """Verify audit log integrity (hash validation, signature checks)"""
        pass
