from agentmesh.aol.coordinator import AgentCoordinator
from agentmesh.mal.router import MessageRouter
from agentmesh.mal.message import UniversalMessage


class Orchestrator:
    def __init__(self, coordinator: AgentCoordinator, router: MessageRouter):
        self.coordinator = coordinator
        self.router = router

    async def assign_task(
        self, task_details: dict, token: str = None, tenant_id: str = None
    ):
        # In a real scenario, this would involve more complex logic
        # to break down the task and assign to workers.
        # Here we just forward it to the coordinator.
        await self.coordinator.coordinate_task(
            task_details, token=token, tenant_id=tenant_id
        )


class Worker:
    def __init__(
        self, agent_id: str, router: MessageRouter, tenant_id: str = "default_tenant"
    ):
        self.agent_id = agent_id
        self.router = router
        self.tenant_id = tenant_id

    async def perform_task(self, task_details: dict):
        print(f"Worker {self.agent_id} is performing task: {task_details}")
        # Simulate task execution
        result = {"status": "completed", "result": "some_result"}
        response_message = UniversalMessage(
            payload=result,
            routing={"targets": ["nats:orchestrator.results"]},
            tenant_id=self.tenant_id,  # Include tenant_id in response
        )
        await self.router.route_message(response_message)
