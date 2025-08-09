from typing import Dict, List, Any
from agentmesh.aol.agent import Agent


class AgentRegistry:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}

    def register_agent(self, agent: Agent):
        self.agents[agent.id] = agent

    def unregister_agent(self, agent_id: str):
        if agent_id in self.agents:
            del self.agents[agent_id]

    def discover_agents(
        self, requirements: Dict[str, Any], tenant_id: str = None
    ) -> List[Agent]:
        # Simple discovery for now, filters by tenant_id if provided
        if tenant_id:
            return [
                agent for agent in self.agents.values() if agent.tenant_id == tenant_id
            ]
        return list(self.agents.values())
