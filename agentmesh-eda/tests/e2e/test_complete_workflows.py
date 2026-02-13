"""
End-to-End Tests: Complete User Journeys

Tests full user workflows through the entire system.

Architectural Intent:
- Verify complete agent lifecycle from creation to termination
- Verify multi-agent collaboration workflows
- Verify system recovery from failures
- Verify tenant isolation throughout entire journeys
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from agentmesh.application.use_cases.create_agent_use_case import (
    CreateAgentUseCase,
    CreateAgentDTO,
)
from agentmesh.domain.entities.agent_aggregate import AgentAggregate
from agentmesh.domain.value_objects.agent_value_objects import AgentId, AgentCapability
from agentmesh.domain.domain_events.agent_events import (
    AgentCreatedEvent,
    AgentTaskAssignedEvent,
    AgentTaskCompletedEvent,
    AgentTerminatedEvent,
)
from tests.integration.application.test_create_agent_use_case import (
    InMemoryAgentRepository,
    InMemoryEventBus,
)


class MockTask:
    """Mock task for testing"""

    def __init__(self, task_id: str, data: dict):
        self.task_id = task_id
        self.data = data
        self.assigned_agent = None
        self.completed = False
        self.result = None


class MockTaskOrchestrator:
    """Mock task orchestrator for E2E tests"""

    def __init__(self):
        self.tasks = {}
        self.assignments = []

    def create_task(self, task_id: str, data: dict):
        task = MockTask(task_id, data)
        self.tasks[task_id] = task
        return task

    def assign_task(self, task_id: str, agent_id: str):
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.assigned_agent = agent_id
            self.assignments.append(
                {"task_id": task_id, "agent_id": agent_id, "assigned_at": "now"}
            )
            return task

    def complete_task(self, task_id: str, result: dict):
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.completed = True
            task.result = result
            return task


@pytest.mark.asyncio
class TestAgentLifecycleE2E:
    """End-to-end tests for complete agent lifecycle"""

    @pytest.fixture
    def setup(self):
        """Setup complete system components"""
        agent_repo = InMemoryAgentRepository()
        event_bus = InMemoryEventBus()
        task_orchestrator = MockTaskOrchestrator()

        create_use_case = CreateAgentUseCase(agent_repo, event_bus)

        return {
            "agent_repo": agent_repo,
            "event_bus": event_bus,
            "task_orchestrator": task_orchestrator,
            "create_use_case": create_use_case,
        }

    async def test_complete_agent_lifecycle(self, setup):
        """Test complete agent lifecycle: create -> assign tasks -> terminate"""
        components = setup

        # Step 1: Create agent
        create_dto = CreateAgentDTO(
            tenant_id="tenant-1",
            agent_id="lifecycle-agent",
            name="Lifecycle Test Agent",
            agent_type="processor",
            capabilities=[{"name": "data_processing", "level": 4}],
            metadata={"test": "lifecycle"},
        )

        agent_result = await components["create_use_case"].execute(create_dto)

        # Verify agent created
        assert agent_result.agent_id == "lifecycle-agent"
        assert agent_result.status == "AVAILABLE"

        # Verify event published
        assert len(components["event_bus"].events) == 1
        creation_event = components["event_bus"].events[0].agent_created_event
        assert isinstance(creation_event, AgentCreatedEvent)

        # Step 2: Load agent and simulate task assignment
        saved_agent = await components["agent_repo"].get_by_id(
            "lifecycle-agent", "tenant-1"
        )
        assert saved_agent is not None

        # Simulate task assignment
        task = components["task_orchestrator"].create_task(
            "task-1", {"type": "process_data"}
        )
        assigned_task = components["task_orchestrator"].assign_task(
            "task-1", "lifecycle-agent"
        )

        # Agent should be busy now
        busy_agent = saved_agent.assign_task(task.task_id)
        assert busy_agent.status == "BUSY"

        # Step 3: Complete task
        completed_task = components["task_orchestrator"].complete_task(
            "task-1", {"status": "success"}
        )

        # Agent should be available again
        available_agent = busy_agent.complete_task()
        assert available_agent.status == "AVAILABLE"

        # Step 4: Terminate agent
        terminated_agent = available_agent.terminate()

        # Verify termination
        assert terminated_agent.status == "TERMINATED"

        # Persist terminated state
        await components["agent_repo"].save(terminated_agent)

        # Verify agent in repository reflects final state
        final_agent = await components["agent_repo"].get_by_id(
            "lifecycle-agent", "tenant-1"
        )
        assert final_agent.status == "TERMINATED"

    async def test_multi_agent_collaboration_workflow(self, setup):
        """Test multi-agent collaboration workflow"""
        components = setup

        # Create multiple agents with different capabilities
        agents = []
        for i, (name, capabilities) in enumerate(
            [
                ("Data Processor", [{"name": "data_processing", "level": 4}]),
                ("Analyzer", [{"name": "analysis", "level": 3}]),
                ("Reporter", [{"name": "reporting", "level": 2}]),
            ]
        ):
            dto = CreateAgentDTO(
                tenant_id="tenant-1",
                agent_id=f"collab-agent-{i}",
                name=name,
                capabilities=capabilities,
                metadata={"collaboration": "test"},
            )
            result = await components["create_use_case"].execute(dto)
            agents.append(result)

        # Verify all agents created
        assert len(agents) == 3

        # Create workflow tasks requiring collaboration
        workflow_tasks = []

        # Task 1: Data processing (requires data_processing capability)
        task1 = components["task_orchestrator"].create_task(
            "workflow-task-1", {"type": "process_data", "requires": ["data_processing"]}
        )
        components["task_orchestrator"].assign_task("workflow-task-1", "collab-agent-0")
        workflow_tasks.append(task1)

        # Task 2: Analysis (requires analysis capability)
        task2 = components["task_orchestrator"].create_task(
            "workflow-task-2", {"type": "analyze_data", "requires": ["analysis"]}
        )
        components["task_orchestrator"].assign_task("workflow-task-2", "collab-agent-1")
        workflow_tasks.append(task2)

        # Task 3: Reporting (requires reporting capability)
        task3 = components["task_orchestrator"].create_task(
            "workflow-task-3", {"type": "generate_report", "requires": ["reporting"]}
        )
        components["task_orchestrator"].assign_task("workflow-task-3", "collab-agent-2")
        workflow_tasks.append(task3)

        # Complete all tasks
        for task in workflow_tasks:
            components["task_orchestrator"].complete_task(
                task.task_id, {"status": "completed"}
            )

        # Verify workflow completed successfully
        assert all(task.completed for task in workflow_tasks)

        # Verify events were published for all agent operations
        assert len(components["event_bus"].events) >= 3  # At least creation events

    async def test_system_recovery_after_failure(self, setup):
        """Test system recovery after agent failure"""
        components = setup

        # Create agent
        dto = CreateAgentDTO(
            tenant_id="tenant-1",
            agent_id="recovery-agent",
            name="Recovery Test Agent",
            capabilities=[{"name": "data_processing", "level": 4}],
        )

        agent_result = await components["create_use_case"].execute(dto)

        # Load agent for simulation
        agent = await components["agent_repo"].get_by_id("recovery-agent", "tenant-1")

        # Simulate task assignment and failure
        task = components["task_orchestrator"].create_task(
            "failure-task", {"type": "process_data"}
        )
        assigned_agent = agent.assign_task(task.task_id)

        # Simulate task failure
        failed_agent = assigned_agent.fail_task("Processing failed")

        # Agent should still be available after failure (not terminated)
        assert failed_agent.status == "AVAILABLE"
        assert failed_agent.get_success_rate() == 0.0  # 0/1 = 0%

        # Agent should be able to handle new tasks
        recovery_task = components["task_orchestrator"].create_task(
            "recovery-task", {"type": "process_data"}
        )
        recovered_agent = failed_agent.assign_task(recovery_task.task_id)

        # Complete recovery task successfully
        final_agent = recovered_agent.complete_task()

        # Agent should have improved success rate
        assert final_agent.get_success_rate() == 0.5  # 1/2 = 50%

    async def test_tenant_isolation_throughout_journey(self, setup):
        """Test tenant isolation throughout complete journey"""
        components = setup

        # Create agents in different tenants
        tenant1_agent_result = await components["create_use_case"].execute(
            CreateAgentDTO(
                tenant_id="tenant-1",
                agent_id="isolated-agent",
                name="Tenant 1 Agent",
                capabilities=[{"name": "processing", "level": 3}],
            )
        )

        tenant2_agent_result = await components["create_use_case"].execute(
            CreateAgentDTO(
                tenant_id="tenant-2",
                agent_id="isolated-agent",  # Same ID, different tenant
                name="Tenant 2 Agent",
                capabilities=[{"name": "processing", "level": 3}],
            )
        )

        # Verify tenant isolation in creation
        assert tenant1_agent_result.tenant_id == "tenant-1"
        assert tenant2_agent_result.tenant_id == "tenant-2"

        # Load agents separately
        agent1 = await components["agent_repo"].get_by_id("isolated-agent", "tenant-1")
        agent2 = await components["agent_repo"].get_by_id("isolated-agent", "tenant-2")

        # Verify they are different
        assert agent1.name == "Tenant 1 Agent"
        assert agent2.name == "Tenant 2 Agent"

        # Create tasks for each tenant
        task1 = components["task_orchestrator"].create_task(
            "tenant1-task", {"tenant": "tenant-1"}
        )
        task2 = components["task_orchestrator"].create_task(
            "tenant2-task", {"tenant": "tenant-2"}
        )

        # Assign tasks to respective agents
        components["task_orchestrator"].assign_task("tenant1-task", "isolated-agent")
        components["task_orchestrator"].assign_task("tenant2-task", "isolated-agent")

        # Complete tasks
        components["task_orchestrator"].complete_task(
            "tenant1-task", {"result": "tenant1_success"}
        )
        components["task_orchestrator"].complete_task(
            "tenant2-task", {"result": "tenant2_success"}
        )

        # Verify tasks handled by correct agents
        assert task1.assigned_agent == "isolated-agent"
        assert task2.assigned_agent == "isolated-agent"
        assert task1.result["result"] == "tenant1_success"
        assert task2.result["result"] == "tenant2_success"


@pytest.mark.asyncio
class TestSystemScalabilityE2E:
    """End-to-end tests for system scalability"""

    @pytest.fixture
    def setup(self):
        """Setup for scalability tests"""
        agent_repo = InMemoryAgentRepository()
        event_bus = InMemoryEventBus()
        task_orchestrator = MockTaskOrchestrator()
        create_use_case = CreateAgentUseCase(agent_repo, event_bus)

        return {
            "agent_repo": agent_repo,
            "event_bus": event_bus,
            "task_orchestrator": task_orchestrator,
            "create_use_case": create_use_case,
        }

    async def test_high_volume_agent_creation(self, setup):
        """Test creating many agents concurrently"""
        components = setup

        # Create many agents concurrently
        create_tasks = []
        for i in range(10):
            dto = CreateAgentDTO(
                tenant_id=f"tenant-{i % 3}",  # 3 tenants
                agent_id=f"scale-agent-{i}",
                name=f"Scale Agent {i}",
                capabilities=[{"name": "processing", "level": i % 5 + 1}],
            )
            task = components["create_use_case"].execute(dto)
            create_tasks.append(task)

        # Execute all creation tasks concurrently
        results = await asyncio.gather(*create_tasks)

        # Verify all agents created
        assert len(results) == 10

        # Verify correct tenant distribution
        tenant_counts = {}
        for result in results:
            tenant_counts[result.tenant_id] = tenant_counts.get(result.tenant_id, 0) + 1

        # Should have agents in all 3 tenants
        assert len(tenant_counts) == 3
        assert all(count > 0 for count in tenant_counts.values())

    async def test_concurrent_task_execution(self, setup):
        """Test concurrent task execution across many agents"""
        components = setup

        # Create agents first
        agents = []
        for i in range(5):
            dto = CreateAgentDTO(
                tenant_id="concurrent-tenant",
                agent_id=f"concurrent-agent-{i}",
                name=f"Concurrent Agent {i}",
                capabilities=[{"name": "processing", "level": 3}],
            )
            result = await components["create_use_case"].execute(dto)
            agents.append(result)

        # Create and assign tasks to all agents
        tasks = []
        for i, agent in enumerate(agents):
            task = components["task_orchestrator"].create_task(
                f"concurrent-task-{i}", {"agent_index": i}
            )
            components["task_orchestrator"].assign_task(
                f"concurrent-task-{i}", agent.agent_id
            )
            tasks.append(task)

        # Execute all tasks concurrently
        execution_tasks = []
        for i, task in enumerate(tasks):
            # Simulate task execution
            async def execute_task(task_data, index):
                await asyncio.sleep(0.01)  # Simulate work
                return components["task_orchestrator"].complete_task(
                    task_data.task_id, {"completed_by": f"agent-{index}"}
                )

            execution_task = execute_task(task, i)
            execution_tasks.append(execution_task)

        # Wait for all executions
        results = await asyncio.gather(*execution_tasks)

        # Verify all tasks completed
        assert len(results) == 5
        assert all(task.completed for task in tasks)

        # Verify agents are back to available state
        for agent_result in agents:
            agent = await components["agent_repo"].get_by_id(
                agent_result.agent_id, "concurrent-tenant"
            )
            assert agent.status == "AVAILABLE"
