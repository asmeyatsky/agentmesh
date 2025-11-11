"""
End-to-End Tests: Agent Workflows

Tests complete workflows from task offering through execution.

Architectural Intent:
- Verify autonomous agents work end-to-end
- Verify collaboration between agents
- Verify task execution workflow
- Verify system resilience
"""

import pytest
import asyncio
from datetime import datetime

from agentmesh.domain.entities.agent_aggregate import AgentAggregate
from agentmesh.domain.value_objects.agent_value_objects import AgentId, AgentCapability
from agentmesh.domain.services.agent_autonomy_service import (
    AgentAutonomyService,
    TaskOffering
)
from agentmesh.domain.services.agent_load_balancer_service import AgentLoadBalancerService
from agentmesh.aol.autonomous_agent import AutonomousAgent


class MockAgentRepository:
    """Mock repository for E2E tests"""
    def __init__(self):
        self.agents = {}

    async def save(self, agent):
        self.agents[agent.agent_id.value] = agent

    async def get_by_id(self, agent_id, tenant_id):
        return self.agents.get(agent_id)


class MockEventBus:
    """Mock event bus for E2E tests"""
    def __init__(self):
        self.events = []

    async def publish(self, event):
        self.events.append(event)


def create_test_agent(agent_id: str,
                     capabilities: list) -> AgentAggregate:
    """Helper to create test agent"""
    caps = [AgentCapability(name=cap["name"], proficiency_level=cap.get("level", 3))
            for cap in capabilities]
    return AgentAggregate(
        agent_id=AgentId(agent_id),
        tenant_id="test-tenant",
        name=f"Test Agent {agent_id}",
        capabilities=caps
    )


def create_test_task(task_id: str,
                    required_capabilities: list,
                    priority: int = 3) -> TaskOffering:
    """Helper to create test task"""
    return TaskOffering(
        task_id=task_id,
        required_capabilities=required_capabilities,
        priority=priority,
        estimated_duration_seconds=60
    )


@pytest.mark.asyncio
class TestAgentWorkflows:
    """End-to-end agent workflow tests"""

    @pytest.fixture
    def setup(self):
        """Setup test environment"""
        repo = MockAgentRepository()
        event_bus = MockEventBus()
        autonomy_service = AgentAutonomyService()
        load_balancer = AgentLoadBalancerService()
        return {
            "repo": repo,
            "event_bus": event_bus,
            "autonomy": autonomy_service,
            "load_balancer": load_balancer
        }

    async def test_agent_accepts_suitable_task(self, setup):
        """Workflow: Agent receives task and accepts it"""
        # Setup
        agent_agg = create_test_agent(
            "agent-1",
            [{"name": "data_processing", "level": 4}]
        )
        agent = AutonomousAgent(
            agent_agg,
            setup["autonomy"],
            setup["load_balancer"],
            setup["repo"],
            setup["event_bus"]
        )
        task = create_test_task(
            "task-1",
            required_capabilities=["data_processing"],
            priority=4
        )

        # Execute
        accepted = await agent.process_task_offerings([task])

        # Verify
        assert len(accepted) == 1
        assert accepted[0] == "task-1"
        assert len(agent.task_queue) == 1

    async def test_agent_rejects_unsuitable_task(self, setup):
        """Workflow: Agent receives task and rejects it"""
        # Setup
        agent_agg = create_test_agent(
            "agent-2",
            [{"name": "data_processing", "level": 2}]  # Low proficiency
        )
        agent = AutonomousAgent(
            agent_agg,
            setup["autonomy"],
            setup["load_balancer"],
            setup["repo"],
            setup["event_bus"]
        )
        task = create_test_task(
            "task-2",
            required_capabilities=["expert_analysis"],  # Different capability
            priority=3
        )

        # Execute
        accepted = await agent.process_task_offerings([task])

        # Verify
        assert len(accepted) == 0
        assert len(agent.task_queue) == 0

    async def test_agent_prioritizes_task_queue(self, setup):
        """Workflow: Agent prioritizes multiple accepted tasks"""
        # Setup
        agent_agg = create_test_agent(
            "agent-3",
            [
                {"name": "data_processing", "level": 4},
                {"name": "analysis", "level": 4},
                {"name": "reporting", "level": 3}
            ]
        )
        agent = AutonomousAgent(
            agent_agg,
            setup["autonomy"],
            setup["load_balancer"],
            setup["repo"],
            setup["event_bus"]
        )

        tasks = [
            create_test_task("task-a", ["data_processing"], priority=2),
            create_test_task("task-b", ["analysis"], priority=5),  # High priority
            create_test_task("task-c", ["reporting"], priority=1),
        ]

        # Execute
        accepted = await agent.process_task_offerings(tasks)

        # Verify - high priority task should be first in queue
        assert len(accepted) == 3
        assert agent.task_queue[0].task_id == "task-b"  # Highest priority first

    async def test_agent_executes_task_queue(self, setup):
        """Workflow: Agent executes tasks sequentially"""
        # Setup
        agent_agg = create_test_agent(
            "agent-4",
            [{"name": "simple_task", "level": 5}]  # High proficiency = high success rate
        )
        agent = AutonomousAgent(
            agent_agg,
            setup["autonomy"],
            setup["load_balancer"],
            setup["repo"],
            setup["event_bus"]
        )

        # Add tasks directly to queue
        task1 = create_test_task("task-1", ["simple_task"], priority=3)
        task2 = create_test_task("task-2", ["simple_task"], priority=3)
        agent.task_queue = [task1, task2]

        # Execute
        results = await agent.execute_tasks()

        # Verify
        assert len(results) == 2
        assert agent.task_queue == []  # Queue empty

    async def test_agent_handles_task_failure(self, setup):
        """Workflow: Agent handles failed task gracefully"""
        # Setup with low success rate to force failures
        agent_agg = create_test_agent(
            "agent-5",
            [{"name": "risky_task", "level": 1}]  # Low proficiency = low success rate
        )
        agent = AutonomousAgent(
            agent_agg,
            setup["autonomy"],
            setup["load_balancer"],
            setup["repo"],
            setup["event_bus"]
        )

        task = create_test_task("task-fail", ["risky_task"], priority=3)
        agent.task_queue = [task]

        # Execute
        results = await agent.execute_tasks()

        # Verify - should handle failure
        assert len(results) >= 1

    async def test_multiple_agents_collaborate(self, setup):
        """Workflow: Multiple agents work on different tasks"""
        # Setup agents
        agent1_agg = create_test_agent(
            "agent-a",
            [{"name": "data_processing", "level": 5}]
        )
        agent2_agg = create_test_agent(
            "agent-b",
            [{"name": "analysis", "level": 5}]
        )

        agent1 = AutonomousAgent(
            agent1_agg,
            setup["autonomy"],
            setup["load_balancer"],
            setup["repo"],
            setup["event_bus"]
        )
        agent2 = AutonomousAgent(
            agent2_agg,
            setup["autonomy"],
            setup["load_balancer"],
            setup["repo"],
            setup["event_bus"]
        )

        # Tasks for each agent
        task1 = create_test_task("task-1", ["data_processing"], priority=3)
        task2 = create_test_task("task-2", ["analysis"], priority=3)

        # Execute
        accepted1 = await agent1.process_task_offerings([task1])
        accepted2 = await agent2.process_task_offerings([task2])

        # Verify - each agent accepts appropriate task
        assert len(accepted1) == 1
        assert len(accepted2) == 1
        assert accepted1[0] == "task-1"
        assert accepted2[0] == "task-2"

    async def test_agent_health_check(self, setup):
        """Workflow: Agent performs health check"""
        # Setup
        agent_agg = create_test_agent(
            "agent-health",
            [{"name": "test", "level": 3}]
        )
        agent = AutonomousAgent(
            agent_agg,
            setup["autonomy"],
            setup["load_balancer"],
            setup["repo"],
            setup["event_bus"]
        )

        # Execute health check
        is_healthy = await agent.check_health()

        # Verify
        assert isinstance(is_healthy, bool)
        assert agent.aggregate.current_metrics is not None

    async def test_agent_workload_management(self, setup):
        """Workflow: Agent manages own workload"""
        # Setup
        agent_agg = create_test_agent(
            "agent-load",
            [{"name": "task", "level": 4}]
        )
        agent = AutonomousAgent(
            agent_agg,
            setup["autonomy"],
            setup["load_balancer"],
            setup["repo"],
            setup["event_bus"]
        )

        # Initially available
        assert agent.should_accept_more_tasks()

        # Add many tasks
        for i in range(10):
            task = create_test_task(f"task-{i}", ["task"])
            agent.task_queue.append(task)

        # Update aggregate to reflect load
        for _ in range(9):
            agent.aggregate = agent.aggregate.assign_task(f"dummy-{_}")

        # Check if should still accept
        workload = agent.get_workload()
        assert 0.0 <= workload <= 1.0

    async def test_agent_pause_and_resume(self, setup):
        """Workflow: Agent can be paused and resumed"""
        # Setup
        agent_agg = create_test_agent(
            "agent-pause",
            [{"name": "task", "level": 3}]
        )
        agent = AutonomousAgent(
            agent_agg,
            setup["autonomy"],
            setup["load_balancer"],
            setup["repo"],
            setup["event_bus"]
        )

        # Add task
        task = create_test_task("task-pause", ["task"])
        await agent.process_task_offerings([task])

        # Pause
        await agent.pause()
        assert agent.aggregate.status == "PAUSED"

        # Resume
        await agent.resume()
        assert agent.aggregate.status == "AVAILABLE"

    async def test_agent_status_summary(self, setup):
        """Workflow: Get agent status summary"""
        # Setup
        agent_agg = create_test_agent(
            "agent-status",
            [{"name": "task", "level": 3}]
        )
        agent = AutonomousAgent(
            agent_agg,
            setup["autonomy"],
            setup["load_balancer"],
            setup["repo"],
            setup["event_bus"]
        )

        # Get status
        status = agent.get_status_summary()

        # Verify
        assert status["agent_id"] == "agent-status"
        assert "status" in status
        assert "workload" in status
        assert "task_queue_size" in status
        assert "success_rate" in status
