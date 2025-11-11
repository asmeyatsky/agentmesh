"""
PostgreSQL Tenant Repository Adapter

Architectural Intent:
- Implements TenantRepositoryPort using PostgreSQL
- Provides tenant authentication and configuration lookup
- Maintains multi-tenancy isolation
- Supports caching and performance optimization

Key Design Decisions:
1. API key lookup uses unique index for performance
2. Tenant status validated on every access (no long-lived cache)
3. Queries filtered by active status to prevent accessing suspended tenants
4. Error handling propagates to caller for graceful degradation
"""

from typing import Optional
from loguru import logger
from agentmesh.domain.ports.tenant_port import (
    TenantRepositoryPort,
    Tenant
)
from agentmesh.db.database import SessionLocal, Tenant as TenantModel


class PostgresTenantAdapter(TenantRepositoryPort):
    """
    PostgreSQL adapter for tenant repository.

    Provides efficient tenant lookup by ID or API key.
    Maintains tenant isolation and configuration access.
    """

    def __init__(self):
        """Initialize adapter with database session"""
        self.Session = SessionLocal
        logger.info("PostgresTenantAdapter initialized")

    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """
        Get active tenant by ID.

        Args:
            tenant_id: Unique tenant identifier

        Returns:
            Tenant if found and active, None otherwise

        Raises:
            Exception: If database access fails
        """
        db = self.Session()
        try:
            db_tenant = db.query(TenantModel).filter(
                TenantModel.id == tenant_id,
                TenantModel.is_active == True
            ).first()

            if not db_tenant:
                logger.debug(f"Tenant {tenant_id} not found or inactive")
                return None

            tenant = Tenant(
                tenant_id=db_tenant.id,
                name=db_tenant.name,
                api_key=db_tenant.api_key,
                is_active=db_tenant.is_active,
                max_agents=db_tenant.max_agents or 100,
                max_messages_per_hour=db_tenant.max_messages_per_hour or 10000,
                features=db_tenant.features or {}
            )

            logger.debug(f"Retrieved tenant {tenant_id}")
            return tenant

        except Exception as e:
            logger.error(f"Failed to retrieve tenant {tenant_id}: {e}")
            raise
        finally:
            db.close()

    async def get_tenant_by_api_key(self, api_key: str) -> Optional[Tenant]:
        """
        Get active tenant by API key.

        Used for API authentication. API key is indexed for performance.

        Args:
            api_key: Tenant API key

        Returns:
            Tenant if found and active, None otherwise

        Raises:
            Exception: If database access fails
        """
        db = self.Session()
        try:
            db_tenant = db.query(TenantModel).filter(
                TenantModel.api_key == api_key,
                TenantModel.is_active == True
            ).first()

            if not db_tenant:
                logger.debug(f"Tenant with API key not found or inactive")
                return None

            tenant = Tenant(
                tenant_id=db_tenant.id,
                name=db_tenant.name,
                api_key=db_tenant.api_key,
                is_active=db_tenant.is_active,
                max_agents=db_tenant.max_agents or 100,
                max_messages_per_hour=db_tenant.max_messages_per_hour or 10000,
                features=db_tenant.features or {}
            )

            logger.debug(f"Retrieved tenant by API key: {db_tenant.id}")
            return tenant

        except Exception as e:
            logger.error(f"Failed to retrieve tenant by API key: {e}")
            raise
        finally:
            db.close()

    async def is_tenant_active(self, tenant_id: str) -> bool:
        """
        Check if tenant is active (not suspended/deleted).

        Quick check without loading full tenant object.

        Args:
            tenant_id: Tenant to check

        Returns:
            True if tenant is active, False otherwise

        Raises:
            Exception: If database access fails
        """
        db = self.Session()
        try:
            exists = db.query(TenantModel).filter(
                TenantModel.id == tenant_id,
                TenantModel.is_active == True
            ).first() is not None

            logger.debug(f"Tenant {tenant_id} active: {exists}")
            return exists

        except Exception as e:
            logger.error(f"Failed to check tenant {tenant_id} status: {e}")
            raise
        finally:
            db.close()

    async def get_tenant_message_limit(self, tenant_id: str) -> int:
        """
        Get hourly message rate limit for tenant.

        Args:
            tenant_id: Tenant to check

        Returns:
            Maximum messages allowed per hour

        Raises:
            Exception: If database access fails or tenant not found
        """
        db = self.Session()
        try:
            db_tenant = db.query(TenantModel).filter(
                TenantModel.id == tenant_id,
                TenantModel.is_active == True
            ).first()

            if not db_tenant:
                logger.warning(f"Tenant {tenant_id} not found for rate limit check")
                raise ValueError(f"Tenant {tenant_id} not found")

            limit = db_tenant.max_messages_per_hour or 10000
            logger.debug(f"Tenant {tenant_id} message limit: {limit}/hour")
            return limit

        except Exception as e:
            logger.error(f"Failed to get message limit for tenant {tenant_id}: {e}")
            raise
        finally:
            db.close()
