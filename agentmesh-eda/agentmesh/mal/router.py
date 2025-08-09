from agentmesh.mal.message import UniversalMessage
from agentmesh.mal.adapters.base import MessagePlatformAdapter
from typing import Dict
from loguru import logger
from agentmesh.utils.metrics import MESSAGES_SENT
from agentmesh.mal.load_balancer import IntelligentLoadBalancer
from agentmesh.security.auth import verify_access_token
from agentmesh.security.roles import UserRole, has_role
from jose import JWTError  # Import JWTError for handling authentication failures


class MessageRouter:
    def __init__(self, tenant_id: str = None):  # Add tenant_id to router
        self.adapters: Dict[str, MessagePlatformAdapter] = {}
        self.load_balancer = IntelligentLoadBalancer()
        self.routing_rules = {
            "event_type_A": ["platform1:topic_A", "platform2:topic_B"],
            "event_type_B": ["platform3:topic_C"],
        }
        self.tenant_id = tenant_id  # Router's tenant_id

    def add_adapter(self, platform: str, adapter: MessagePlatformAdapter):
        self.adapters[platform] = adapter

    async def route_message(self, message: UniversalMessage):
        logger.debug(
            f"Attempting to route message {message.metadata.get('id')} with tenant_id: {message.tenant_id}"
        )
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

            required_roles = [UserRole.AGENT]  # Example: only agents can send messages
            if not has_role(user_roles, required_roles):
                logger.warning(
                    f"Message {message.metadata.get('id')} rejected: User does not have required roles {required_roles}. User roles: {user_roles}"
                )
                return
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

        # Advanced routing based on message type
        message_type = message.metadata.get("type")
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
            # Fallback to original routing if no specific rule matches
            for target in message.routing.get("targets", []):
                platform, topic = target.split(":", 1)
                if platform in self.adapters:
                    logger.info(
                        f"Routing message {message.metadata.get('id')} to {platform}:{topic} via direct target"
                    )
                    await self.adapters[platform].send(message, topic)
                    MESSAGES_SENT.labels(platform=platform, topic=topic).inc()
