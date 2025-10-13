from agentmesh.mal.message import UniversalMessage
from agentmesh.mal.adapters.base import MessagePlatformAdapter
from agentmesh.mal.advanced_router import AdvancedMessageRouter as InternalAdvancedRouter
from agentmesh.aol.registry import AgentRegistry
from typing import Dict
from loguru import logger
from agentmesh.utils.metrics import MESSAGES_SENT
from agentmesh.mal.load_balancer import IntelligentLoadBalancer
from agentmesh.security.auth import verify_access_token
from agentmesh.security.roles import UserRole, has_role
from jose import JWTError  # Import JWTError for handling authentication failures
from agentmesh.db.database import SessionLocal, Message # Import SessionLocal and Message
from agentmesh.security.encryption import encrypt_data, decrypt_data # Import encryption functions


class MessageRouter:
    def __init__(self, tenant_id: str = None, use_advanced_routing: bool = False):  # Add tenant_id to router
        self.adapters: Dict[str, MessagePlatformAdapter] = {}
        self.load_balancer = IntelligentLoadBalancer()
        self.routing_rules = {
            "event_type_A": ["platform1:topic_A", "platform2:topic_B"],
            "event_type_B": ["platform3:topic_C"],
            "priority_high": ["platform_high:high_priority_topic"], # New rule
        }
        self.message_type_roles = {
            "TaskAssigned": [UserRole.ORCHESTRATOR],
            # Add other message types and their required roles here
        }
        self.tenant_id = tenant_id  # Router's tenant_id
        self.use_advanced_routing = use_advanced_routing
        self.advanced_router = None  # Will be initialized when needed
        
        if use_advanced_routing:
            # Initialize the advanced router with agent registry
            registry = AgentRegistry()
            self.advanced_router = InternalAdvancedRouter(registry)

    def add_adapter(self, platform: str, adapter: MessagePlatformAdapter):
        self.adapters[platform] = adapter

    async def route_message(self, message: UniversalMessage):
        logger.debug(
            f"Attempting to route message {message.metadata.get('id')} with tenant_id: {message.tenant_id}"
        )

        # Save message to database
        db = SessionLocal()
        try:
            db_message = Message(
                id=message.metadata.get("id"),
                tenant_id=message.tenant_id,
                payload=encrypt_data(message.serialize()).decode('utf-8') # Encrypt and store as string
            )
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            logger.info(f"Message {message.metadata.get('id')} saved to database.")
        except Exception as e:
            logger.error(f"Failed to save message {message.metadata.get('id')} to database: {e}")
        finally:
            db.close()

        # Tenant filtering
        if self.tenant_id is not None and message.tenant_id != self.tenant_id:
            logger.warning(
                f"Message {message.metadata.get('id')} rejected: Mismatched tenant_id. Router tenant: {self.tenant_id}, Message tenant: {message.tenant_id}"
            )
            return

        logger.debug(f"Tenant filter passed for message {message.metadata.get('id')}")
        # Authentication and Authorization
        token = message.metadata.get("token")
        if not token:
            logger.warning(
                f"Message {message.metadata.get('id')} rejected: No authentication token provided."
            )
            return

        try:
            logger.debug(f"Verifying token for message {message.metadata.get('id')}")

            # Mocking credentials_exception for standalone use
            class CredentialsException(Exception):
                pass

            user_payload = verify_access_token(token, CredentialsException)
            user_roles = [UserRole(role) for role in user_payload.get("roles", [])]
            logger.debug(
                f"User roles for message {message.metadata.get('id')}: {user_roles}"
            )

            # Check role-based authorization for message type
            message_type = message.metadata.get("type")
            required_roles_for_type = self.message_type_roles.get(message_type, [])

            if required_roles_for_type and not has_role(user_roles, required_roles_for_type):
                logger.warning(
                    f"Message {message.metadata.get('id')} rejected: User does not have required roles {required_roles_for_type} for message type {message_type}. User roles: {user_roles}"
                )
                return

            # Original agent role check (can be refined or removed if message_type_roles covers all cases)
            # required_roles = [UserRole.AGENT]  # Example: only agents can send messages
            # if not has_role(user_roles, required_roles):
            #     logger.warning(
            #         f"Message {message.metadata.get('id')} rejected: User does not have required roles {required_roles}. User roles: {user_roles}"
            #     )
            #     return
            logger.debug(
                f"Authorization passed for message {message.metadata.get('id')}"
            )

        except JWTError as e:
            logger.warning(
                f"Message {message.metadata.get('id')} rejected: Invalid authentication token. Error: {e}"
            )
            return
        except CredentialsException:
            logger.warning(
                f"Message {message.metadata.get('id')} rejected: Invalid credentials."
            )
            return
        except Exception as e:
            logger.error(
                f"Unexpected error during authentication/authorization for message {message.metadata.get('id')}: {e}"
            )
            return

        # If advanced routing is enabled, use it for intelligent agent selection
        if self.use_advanced_routing and self.advanced_router:
            target_agent_id = await self.advanced_router.route_message(message)
            if target_agent_id:
                # Route directly to the selected agent
                logger.info(
                    f"Advanced routing selected agent {target_agent_id} for message {message.metadata.get('id')}"
                )
                
                # For direct agent routing, we might send to a specific topic
                # This would depend on the implementation of agent-specific routing
                # For now, we'll send to a general agent processing topic
                platform = "nats"  # Default platform for agent routing
                if platform in self.adapters:
                    await self.adapters[platform].send(message, f"agent.{target_agent_id}")
                    MESSAGES_SENT.labels(platform=platform, topic=f"agent.{target_agent_id}").inc()
                return

        # Advanced routing based on message type or priority
        message_type = message.metadata.get("type")
        message_priority = message.metadata.get("priority")

        if message_priority == "high" and "priority_high" in self.routing_rules:
            targets = self.routing_rules["priority_high"]
            selected_target = self.load_balancer.select_target(targets)
            platform, topic = selected_target.split(":", 1)
            if platform in self.adapters:
                logger.info(
                    f"Routing high priority message {message.metadata.get('id')} to {platform}:{topic}"
                )
                await self.adapters[platform].send(message, topic)
                MESSAGES_SENT.labels(platform=platform, topic=topic).inc()
                return # Message handled by priority rule

        if message_type and message_type in self.routing_rules:
            targets = self.routing_rules[message_type]
            selected_target = self.load_balancer.select_target(targets)
            platform, topic = selected_target.split(":", 1)
            if platform in self.adapters:
                logger.info(
                    f"Routing message {message.metadata.get('id')} (type: {message_type}) to {platform}:{topic} via routing rule"
                )
                await self.adapters[platform].send(message, topic)
                MESSAGES_SENT.labels(platform=platform, topic=topic).inc()
        else:
            # Fallback to original routing if no specific rule matches, using load balancer
            targets = message.routing.get("targets", [])
            if targets:
                selected_target = self.load_balancer.select_target(targets)
                platform, topic = selected_target.split(":", 1)
                if platform in self.adapters:
                    logger.info(
                        f"Routing message {message.metadata.get('id')} to {platform}:{topic} via direct target and load balancer"
                    )
                    await self.adapters[platform].send(message, topic)
                    MESSAGES_SENT.labels(platform=platform, topic=topic).inc()
