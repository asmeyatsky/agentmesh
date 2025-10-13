from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    AGENT = "agent"
    OBSERVER = "observer"
    ORCHESTRATOR = "orchestrator"
    TASK_EXECUTOR = "task_executor"


def has_role(user_roles: list[UserRole], required_roles: list[UserRole]) -> bool:
    if not required_roles:  # If no roles are required, always return True
        return True
    return any(role in user_roles for role in required_roles)
