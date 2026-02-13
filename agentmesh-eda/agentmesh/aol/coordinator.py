from agentmesh.aol.registry import AgentRegistry
from agentmesh.mal.router import MessageRouter
from agentmesh.mal.message import UniversalMessage
from loguru import logger
from agentmesh.aol.workflow_engine import WorkflowEngine # Import WorkflowEngine


class AgentCoordinator:
    def __init__(self, registry: AgentRegistry, router: MessageRouter):
        self.registry = registry
        self.router = router
        self.workflow_engine = WorkflowEngine(registry, router) # Initialize WorkflowEngine

    async def coordinate_task(
        self, task_data: dict, token: str = None, tenant_id: str = None
    ):
        """Find a capable agent and route a task to it."""
        capability = task_data.get("capability")
        agents = self.registry.discover_agents(requirements=[capability], tenant_id=tenant_id)
        if not agents:
            raise ValueError(f"No agent found with capability '{capability}' in tenant '{tenant_id}'")

        agent = agents[0]
        message = UniversalMessage(
            payload=task_data,
            routing={"targets": [f"nats:agent.{agent.id}.tasks"]},
            metadata={"token": token, "type": "TaskAssigned"},
        )
        message.tenant_id = tenant_id

        # Send directly to the agent's task queue
        target = f"agent.{agent.id}.tasks"
        for platform, adapter in self.router.adapters.items():
            await adapter.send(message, target)
            break

    async def execute_workflow(
        self, workflow_type: str, workflow_data: dict, token: str = None, tenant_id: str = None
    ):
        await self.workflow_engine.execute_workflow(workflow_type, workflow_data, token, tenant_id)
