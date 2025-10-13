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

    async def execute_workflow(
        self, workflow_type: str, workflow_data: dict, token: str = None, tenant_id: str = None
    ):
        await self.workflow_engine.execute_workflow(workflow_type, workflow_data, token, tenant_id)
