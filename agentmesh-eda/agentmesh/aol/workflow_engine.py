from abc import ABC, abstractmethod
from typing import Dict, Any, List
from loguru import logger

from agentmesh.aol.registry import AgentRegistry
from agentmesh.mal.router import MessageRouter
from agentmesh.mal.message import UniversalMessage
from agentmesh.aol.agent import Agent


class WorkflowPattern(ABC):
    """Base class for all workflow patterns."""

    def __init__(self, registry: AgentRegistry, router: MessageRouter):
        self.registry = registry
        self.router = router

    @abstractmethod
    async def execute(self, workflow_data: Dict[str, Any], token: str = None, tenant_id: str = None):
        pass


class OrchestratorWorkerWorkflow(WorkflowPattern):
    async def execute(self, workflow_data: Dict[str, Any], token: str = None, tenant_id: str = None):
        logger.info(f"Executing Orchestrator-Worker workflow for tenant: {tenant_id}")
        orchestrator_requirements = workflow_data.get("orchestrator_requirements", [])
        worker_requirements = workflow_data.get("worker_requirements", [])
        task_payload = workflow_data.get("task_payload", {})

        # Discover orchestrator agent
        orchestrators = self.registry.discover_agents(orchestrator_requirements, tenant_id=tenant_id)
        if not orchestrators:
            logger.warning(f"No orchestrator agent found for tenant: {tenant_id} with requirements: {orchestrator_requirements}")
            return

        orchestrator_agent = orchestrators[0] # Assuming one orchestrator for simplicity
        logger.info(f"Selected orchestrator: {orchestrator_agent.id}")

        # Send task to orchestrator
        message = UniversalMessage(
            payload={"command": "start_orchestration", "task": task_payload, "worker_requirements": worker_requirements},
            routing={"targets": [f"nats:agent.{orchestrator_agent.id}.commands"]},
            metadata={"token": token} if token else {},
            tenant_id=tenant_id if tenant_id else "default_tenant",
        )
        await self.router.route_message(message)
        logger.info(f"Sent orchestration command to {orchestrator_agent.id}")


class HierarchicalWorkflow(WorkflowPattern):
    async def execute(self, workflow_data: Dict[str, Any], token: str = None, tenant_id: str = None):
        logger.info(f"Executing Hierarchical workflow for tenant: {tenant_id}")
        # Example: Find a strategic agent and assign a high-level goal
        strategic_requirements = workflow_data.get("strategic_requirements", [])
        goal_payload = workflow_data.get("goal_payload", {})

        strategic_agents = self.registry.discover_agents(strategic_requirements, tenant_id=tenant_id)
        if not strategic_agents:
            logger.warning(f"No strategic agent found for tenant: {tenant_id} with requirements: {strategic_requirements}")
            return

        strategic_agent = strategic_agents[0]
        logger.info(f"Selected strategic agent: {strategic_agent.id}")

        message = UniversalMessage(
            payload={"command": "set_strategic_goal", "goal": goal_payload},
            routing={"targets": [f"nats:agent.{strategic_agent.id}.commands"]},
            metadata={"token": token} if token else {},
            tenant_id=tenant_id if tenant_id else "default_tenant",
        )
        await self.router.route_message(message)
        logger.info(f"Sent strategic goal to {strategic_agent.id}")


class BlackboardWorkflow(WorkflowPattern):
    async def execute(self, workflow_data: Dict[str, Any], token: str = None, tenant_id: str = None):
        logger.info(f"Executing Blackboard workflow for tenant: {tenant_id}")
        # Example: Post initial data to the blackboard topic
        initial_data = workflow_data.get("initial_data", {})
        blackboard_topic = workflow_data.get("blackboard_topic", "blackboard.knowledge")

        message = UniversalMessage(
            payload={"command": "post_initial_data", "data": initial_data},
            routing={"targets": [f"nats:{blackboard_topic}"]},
            metadata={"token": token} if token else {},
            tenant_id=tenant_id if tenant_id else "default_tenant",
        )
        await self.router.route_message(message)
        logger.info(f"Posted initial data to blackboard topic: {blackboard_topic}")


class MarketBasedWorkflow(WorkflowPattern):
    async def execute(self, workflow_data: Dict[str, Any], token: str = None, tenant_id: str = None):
        logger.info(f"Executing Market-Based workflow for tenant: {tenant_id}")
        # Example: Initiate a bidding process for a resource
        resource_description = workflow_data.get("resource_description", {})
        bidding_topic = workflow_data.get("bidding_topic", "market.bids.default")

        message = UniversalMessage(
            payload={"command": "request_bids", "resource": resource_description},
            routing={"targets": [f"nats:{bidding_topic}"]},
            metadata={"token": token} if token else {},
            tenant_id=tenant_id if tenant_id else "default_tenant",
        )
        await self.router.route_message(message)
        logger.info(f"Initiated bidding process on topic: {bidding_topic}")


class WorkflowEngine:
    def __init__(self, registry: AgentRegistry, router: MessageRouter):
        self.patterns: Dict[str, WorkflowPattern] = {
            "orchestrator_worker": OrchestratorWorkerWorkflow(registry, router),
            "hierarchical": HierarchicalWorkflow(registry, router),
            "blackboard": BlackboardWorkflow(registry, router),
            "market_based": MarketBasedWorkflow(registry, router),
        }

    async def execute_workflow(self, workflow_type: str, workflow_data: Dict[str, Any], token: str = None, tenant_id: str = None):
        pattern = self.patterns.get(workflow_type)
        if not pattern:
            logger.error(f"Unknown workflow type: {workflow_type}")
            return

        await pattern.execute(workflow_data, token, tenant_id)