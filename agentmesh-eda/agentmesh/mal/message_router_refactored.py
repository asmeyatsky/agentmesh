"""
Refactored Message Router

Architectural Intent:
- Routes messages to appropriate agents/topics
- Uses ports/adapters for all external dependencies
- Enforces multi-tenancy and authentication
- Maintains separation of concerns
- Extensible for custom routing strategies

Key Design Decisions:
1. All external dependencies injected via constructor (testability)
2. Routing logic separated from persistence logic
3. Tenant validation delegated to port
4. Message persistence optional (can disable for performance)
5. Advanced routing delegated to strategy classes
"""

from typing import Dict, Optional, Callable
from dataclasses import dataclass
from loguru import logger

from agentmesh.mal.message import UniversalMessage
from agentmesh.mal.adapters.base import MessagePlatformAdapter
from agentmesh.mal.load_balancer import IntelligentLoadBalancer
from agentmesh.domain.ports.message_persistence_port import MessagePersistencePort
from agentmesh.domain.ports.tenant_port import TenantRepositoryPort
from agentmesh.security.auth import verify_access_token
from agentmesh.security.roles import UserRole, has_role
from agentmesh.utils.metrics import MESSAGES_SENT
from jose import JWTError


@dataclass(frozen=True)
class RoutingContext:
    """
    Immutable routing context for a single message.

    Captures all relevant information for routing decision.
    """
    message_id: str
    tenant_id: str
    message_type: str
    priority: str
    source: str
    user_roles: list
    is_authenticated: bool


class MessageRoutingStrategy:
    """Base class for routing strategies"""

    async def route(self,
                   message: UniversalMessage,
                   context: RoutingContext,
                   adapters: Dict[str, MessagePlatformAdapter],
                   load_balancer: IntelligentLoadBalancer) -> bool:
        """
        Attempt to route message using this strategy.

        Args:
            message: Message to route
            context: Routing context
            adapters: Available message adapters
            load_balancer: Load balancer for target selection

        Returns:
            True if message was routed, False otherwise
        """
        raise NotImplementedError


class PriorityRoutingStrategy(MessageRoutingStrategy):
    """Routes high-priority messages to dedicated topic"""

    def __init__(self, rules: Dict[str, list]):
        self.rules = rules

    async def route(self,
                   message: UniversalMessage,
                   context: RoutingContext,
                   adapters: Dict[str, MessagePlatformAdapter],
                   load_balancer: IntelligentLoadBalancer) -> bool:
        """Route high-priority messages"""
        if context.priority != "high":
            return False

        if "priority_high" not in self.rules:
            return False

        targets = self.rules["priority_high"]
        selected_target = load_balancer.select_target(targets)
        platform, topic = selected_target.split(":", 1)

        if platform not in adapters:
            logger.warning(f"Platform {platform} not available for high-priority routing")
            return False

        logger.info(f"Routing high-priority message {context.message_id} to {platform}:{topic}")
        await adapters[platform].send(message, topic)
        MESSAGES_SENT.labels(platform=platform, topic=topic).inc()

        return True


class TypeBasedRoutingStrategy(MessageRoutingStrategy):
    """Routes messages based on type"""

    def __init__(self, rules: Dict[str, list]):
        self.rules = rules

    async def route(self,
                   message: UniversalMessage,
                   context: RoutingContext,
                   adapters: Dict[str, MessagePlatformAdapter],
                   load_balancer: IntelligentLoadBalancer) -> bool:
        """Route based on message type"""
        if context.message_type not in self.rules:
            return False

        targets = self.rules[context.message_type]
        selected_target = load_balancer.select_target(targets)
        platform, topic = selected_target.split(":", 1)

        if platform not in adapters:
            logger.warning(f"Platform {platform} not available for type-based routing")
            return False

        logger.info(f"Routing message {context.message_id} (type: {context.message_type}) to {platform}:{topic}")
        await adapters[platform].send(message, topic)
        MESSAGES_SENT.labels(platform=platform, topic=topic).inc()

        return True


class DefaultRoutingStrategy(MessageRoutingStrategy):
    """Fallback routing strategy using message targets"""

    async def route(self,
                   message: UniversalMessage,
                   context: RoutingContext,
                   adapters: Dict[str, MessagePlatformAdapter],
                   load_balancer: IntelligentLoadBalancer) -> bool:
        """Route using message targets"""
        targets = message.routing.get("targets", [])
        if not targets:
            logger.warning(f"Message {context.message_id} has no routing targets")
            return False

        selected_target = load_balancer.select_target(targets)
        platform, topic = selected_target.split(":", 1)

        if platform not in adapters:
            logger.warning(f"Platform {platform} not available")
            return False

        logger.info(f"Routing message {context.message_id} to {platform}:{topic} (default strategy)")
        await adapters[platform].send(message, topic)
        MESSAGES_SENT.labels(platform=platform, topic=topic).inc()

        return True


class MessageRouter:
    """
    Refactored message router with dependency injection.

    Responsibilities:
    - Validate messages (authentication, authorization)
    - Persist messages for audit trail (optional)
    - Route messages to appropriate targets
    - Track routing metrics
    """

    def __init__(self,
                 tenant_repository: TenantRepositoryPort,
                 message_persistence: Optional[MessagePersistencePort] = None,
                 routing_rules: Optional[Dict[str, list]] = None,
                 message_type_roles: Optional[Dict[str, list]] = None):
        """
        Initialize router with dependencies.

        Args:
            tenant_repository: Port for tenant validation
            message_persistence: Optional port for message persistence
            routing_rules: Optional custom routing rules
            message_type_roles: Optional role requirements per message type
        """
        self.tenant_repo = tenant_repository
        self.message_persistence = message_persistence
        self.adapters: Dict[str, MessagePlatformAdapter] = {}
        self.load_balancer = IntelligentLoadBalancer()
        self.routing_rules = routing_rules or {}
        self.message_type_roles = message_type_roles or {}

        # Initialize routing strategies (ordered by priority)
        self.routing_strategies = [
            PriorityRoutingStrategy(self.routing_rules),
            TypeBasedRoutingStrategy(self.routing_rules),
            DefaultRoutingStrategy()
        ]

        logger.info("MessageRouter initialized with dependency injection")

    def add_adapter(self, platform: str, adapter: MessagePlatformAdapter):
        """Register a message adapter"""
        self.adapters[platform] = adapter
        logger.debug(f"Registered adapter for platform: {platform}")

    async def route_message(self, message: UniversalMessage):
        """
        Route a message to appropriate targets.

        Process:
        1. Validate tenant existence and status
        2. Authenticate and authorize sender
        3. Optionally persist for audit trail
        4. Apply routing strategies in order
        5. Track metrics

        Args:
            message: Message to route

        Raises:
            ValueError: If message is invalid
            JWTError: If authentication fails
        """
        message_id = message.metadata.get("id", "unknown")
        tenant_id = message.tenant_id

        logger.debug(f"Processing message {message_id} for tenant {tenant_id}")

        # Step 1: Validate tenant
        tenant = await self.tenant_repo.get_tenant(tenant_id)
        if not tenant:
            logger.warning(f"Message {message_id} rejected: Tenant {tenant_id} not found or inactive")
            return

        # Step 2: Authenticate and authorize
        try:
            context = await self._validate_authentication(message, message_id)
        except (JWTError, ValueError) as e:
            logger.warning(f"Message {message_id} rejected: Authentication failed - {e}")
            return

        # Step 3: Optionally persist
        if self.message_persistence:
            try:
                await self.message_persistence.persist_message(message)
                logger.debug(f"Message {message_id} persisted for audit trail")
            except Exception as e:
                logger.warning(f"Failed to persist message {message_id}: {e}")
                # Continue routing even if persistence fails

        # Step 4: Route using strategies
        routed = False
        for strategy in self.routing_strategies:
            try:
                if await strategy.route(message, context, self.adapters, self.load_balancer):
                    routed = True
                    break
            except Exception as e:
                logger.error(f"Routing strategy failed for message {message_id}: {e}")
                continue

        if not routed:
            logger.warning(f"Message {message_id} could not be routed by any strategy")

    async def _validate_authentication(self,
                                       message: UniversalMessage,
                                       message_id: str) -> RoutingContext:
        """
        Validate authentication and authorization.

        Returns:
            RoutingContext with user roles and authentication status

        Raises:
            ValueError: If token is missing
            JWTError: If token is invalid
        """
        token = message.metadata.get("token")
        if not token:
            raise ValueError("No authentication token provided")

        # Verify JWT token
        class CredentialsException(Exception):
            pass

        user_payload = verify_access_token(token, CredentialsException)
        user_roles = [UserRole(role) for role in user_payload.get("roles", [])]

        # Check role-based authorization for message type
        message_type = message.metadata.get("type", "UNKNOWN")
        required_roles = self.message_type_roles.get(message_type, [])

        if required_roles and not has_role(user_roles, required_roles):
            raise PermissionError(
                f"User does not have required roles {required_roles} for message type {message_type}"
            )

        logger.debug(f"Message {message_id} passed authentication/authorization")

        return RoutingContext(
            message_id=message_id,
            tenant_id=message.tenant_id,
            message_type=message_type,
            priority=message.metadata.get("priority", "NORMAL"),
            source=message.metadata.get("source", "UNKNOWN"),
            user_roles=user_roles,
            is_authenticated=True
        )
