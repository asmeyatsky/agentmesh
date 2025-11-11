"""
Message Persistence Port

Architectural Intent:
- Defines interface for persisting messages to storage
- Separates infrastructure concerns (database) from routing logic
- Enables multiple storage implementations (PostgreSQL, S3, event store)
- Supports audit trail and message history

Key Design Decisions:
1. Port interface defined in domain layer (not infrastructure)
2. Async/await for non-blocking operations
3. Rich error handling with custom exceptions
4. Immutable persistence results
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from agentmesh.mal.message import UniversalMessage


@dataclass(frozen=True)
class MessagePersistenceResult:
    """
    Result of message persistence operation

    Invariants:
    - persisted_id is always set on success
    - persisted_at timestamp is always recent
    """
    persisted_id: str
    tenant_id: str
    persisted_at: datetime
    storage_location: str


class MessagePersistenceException(Exception):
    """Base exception for message persistence errors"""
    pass


class MessageNotPersistedException(MessagePersistenceException):
    """Raised when message cannot be persisted"""
    pass


class MessagePersistencePort(ABC):
    """
    Port: Store and retrieve messages for audit/replay purposes.

    Responsibilities:
    - Persist messages with encryption for sensitive data
    - Support message history queries
    - Enable message replay for recovery
    - Maintain message ordering per tenant
    """

    @abstractmethod
    async def persist_message(self,
                            message: UniversalMessage) -> MessagePersistenceResult:
        """
        Persist message to storage.

        Args:
            message: UniversalMessage to persist

        Returns:
            MessagePersistenceResult with storage details

        Raises:
            MessagePersistenceException: If persistence fails
            ValueError: If message is invalid
        """
        pass

    @abstractmethod
    async def get_message(self,
                         message_id: str,
                         tenant_id: str) -> Optional[UniversalMessage]:
        """
        Retrieve persisted message.

        Args:
            message_id: ID of message to retrieve
            tenant_id: Tenant ID for isolation

        Returns:
            UniversalMessage if found, None otherwise

        Raises:
            MessagePersistenceException: If retrieval fails
        """
        pass

    @abstractmethod
    async def get_message_history(self,
                                 tenant_id: str,
                                 limit: int = 100,
                                 offset: int = 0) -> List[UniversalMessage]:
        """
        Retrieve message history for tenant.

        Args:
            tenant_id: Tenant ID for isolation
            limit: Maximum messages to return
            offset: Number of messages to skip

        Returns:
            List of UniversalMessage ordered by timestamp DESC

        Raises:
            MessagePersistenceException: If query fails
        """
        pass

    @abstractmethod
    async def get_messages_by_type(self,
                                  message_type: str,
                                  tenant_id: str,
                                  limit: int = 100) -> List[UniversalMessage]:
        """
        Retrieve messages by type.

        Args:
            message_type: Type of message to filter by
            tenant_id: Tenant ID for isolation
            limit: Maximum messages to return

        Returns:
            List of UniversalMessage matching type

        Raises:
            MessagePersistenceException: If query fails
        """
        pass

    @abstractmethod
    async def delete_message(self,
                           message_id: str,
                           tenant_id: str) -> bool:
        """
        Delete persisted message.

        Args:
            message_id: ID of message to delete
            tenant_id: Tenant ID for isolation

        Returns:
            True if deleted, False if not found

        Raises:
            MessagePersistenceException: If deletion fails
        """
        pass
