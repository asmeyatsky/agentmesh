from typing import Dict, Any
from loguru import logger

class AgentStatusReadModel:
    def __init__(self):
        # In a real application, this would be backed by a persistent store (e.g., PostgreSQL, Redis)
        self._agent_statuses: Dict[str, Dict[str, Any]] = {} # Key: "tenant_id:agent_id", Value: {"status": "...", "last_update": "..."}

    def update_agent_status(self, tenant_id: str, agent_id: str, status: str, last_update: str):
        key = f"{tenant_id}:{agent_id}"
        self._agent_statuses[key] = {"status": status, "last_update": last_update}
        logger.info(f"Updated agent status for {agent_id} in tenant {tenant_id} to {status}")

    def get_agent_status(self, tenant_id: str, agent_id: str) -> Dict[str, Any]:
        key = f"{tenant_id}:{agent_id}"
        return self._agent_statuses.get(key, {"status": "not_found", "last_update": None})

    def get_all_agent_statuses(self) -> Dict[str, Dict[str, Any]]:
        return self._agent_statuses