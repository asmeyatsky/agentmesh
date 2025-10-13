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
        self, requirements: List[str] = None, tenant_id: str = None
    ) -> List[Agent]:
        # Discover agents based on capabilities and tenant_id
        found_agents = []
        for agent in self.agents.values():
            if tenant_id and agent.tenant_id != tenant_id:
                continue  # Skip if tenant_id does not match

            if requirements:
                # Check if the agent has all required capabilities
                if all(req in agent.capabilities for req in requirements):
                    found_agents.append(agent)
            else:
                # If no specific requirements, add all agents (after tenant_id filter)
                found_agents.append(agent)
        return found_agents
