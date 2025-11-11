"""
Agent Collaboration Service

Architectural Intent:
- Enable multi-agent coordination and collaboration
- Decompose complex tasks into subtasks
- Facilitate agent negotiation and resource allocation
- Resolve conflicts in distributed decision-making
- Support collaborative problem-solving

Key Design Decisions:
1. Collaboration is domain logic, not infrastructure
2. Uses graph algorithms for task decomposition
3. Supports multiple negotiation strategies
4. Tracks collaboration metrics for optimization
5. Events for other systems to react to
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Set
from loguru import logger

from agentmesh.domain.entities.agent_aggregate import AgentAggregate
from agentmesh.domain.services.agent_load_balancer_service import AgentLoadBalancerService


@dataclass
class SubTask:
    """Subtask within decomposed work"""
    subtask_id: str
    description: str
    required_capabilities: List[str]
    estimated_duration_seconds: int
    dependencies: List[str] = None  # IDs of subtasks that must complete first
    assigned_agent_id: Optional[str] = None
    priority: int = 3  # 1-5


@dataclass
class CollaborationNegotiation:
    """Record of negotiation between agents"""
    negotiation_id: str
    initiating_agent_id: str
    target_agent_id: str
    resource_request: Dict  # What's being negotiated
    status: str  # PENDING, AGREED, REJECTED, COMPLETED
    agreements: Dict = None  # Terms agreed upon


@dataclass
class AgentConflict:
    """Conflict between agents"""
    conflict_id: str
    agent_ids: List[str]  # Agents involved
    conflict_type: str  # RESOURCE, SCHEDULING, STATE
    description: str
    resolution: Optional[str] = None


class AgentCollaborationService:
    """
    Domain Service: Coordinate multiple agents.

    Handles:
    - Task decomposition (break complex work)
    - Agent negotiation (allocate resources)
    - Conflict resolution (handle disagreements)
    - Collaboration tracking (metrics)
    """

    def __init__(self, load_balancer: AgentLoadBalancerService):
        """
        Initialize collaboration service.

        Args:
            load_balancer: For agent selection during collaboration
        """
        self.load_balancer = load_balancer
        logger.info("AgentCollaborationService initialized")

    # ==================== Task Decomposition ====================

    async def decompose_complex_task(self,
                                     task_description: str,
                                     task_subtasks: List[Dict],
                                     available_agents: List[AgentAggregate]) -> List[SubTask]:
        """
        Decompose complex task into subtasks.

        Algorithm:
        1. Parse task dependencies (build DAG)
        2. Create subtasks
        3. Perform topological sort for execution order
        4. Assign agents to subtasks based on capabilities
        5. Return ordered subtasks with assignments

        Args:
            task_description: Description of complex task
            task_subtasks: List of subtask specifications
            available_agents: Agents available for assignment

        Returns:
            List of SubTasks with agent assignments

        Raises:
            ValueError: If task cannot be decomposed (no qualified agents)
        """
        logger.info(f"Decomposing complex task: {task_description}")

        # Step 1: Build dependency graph (DAG)
        subtasks_by_id = {}
        dependencies = {}

        for subtask_spec in task_subtasks:
            subtask = SubTask(
                subtask_id=subtask_spec["id"],
                description=subtask_spec.get("description", ""),
                required_capabilities=subtask_spec.get("required_capabilities", []),
                estimated_duration_seconds=subtask_spec.get("duration_seconds", 300),
                dependencies=subtask_spec.get("dependencies", []),
                priority=subtask_spec.get("priority", 3)
            )
            subtasks_by_id[subtask.subtask_id] = subtask
            dependencies[subtask.subtask_id] = subtask.dependencies or []

        # Step 2: Topological sort to determine execution order
        ordered_subtask_ids = self._topological_sort(dependencies)
        ordered_subtasks = [subtasks_by_id[id_] for id_ in ordered_subtask_ids]

        # Step 3: Assign agents to subtasks
        for subtask in ordered_subtasks:
            best_agent = self.load_balancer.select_best_agent(
                subtask.required_capabilities,
                available_agents
            )

            if not best_agent:
                raise ValueError(
                    f"No agent available for subtask {subtask.subtask_id} "
                    f"(required: {subtask.required_capabilities})"
                )

            subtask.assigned_agent_id = best_agent.agent_id.value
            logger.info(
                f"Assigned subtask {subtask.subtask_id} to agent {best_agent.agent_id.value}"
            )

        return ordered_subtasks

    # ==================== Resource Negotiation ====================

    async def negotiate_resource_allocation(self,
                                           agents: List[AgentAggregate],
                                           resource_needs: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Facilitate negotiation for shared resources.

        Algorithm:
        1. Each agent states needs
        2. Check if total > available
        3. If so, agents negotiate (reduce requests)
        4. Continue until agreement or failure

        Args:
            agents: Agents participating
            resource_needs: Dict of {agent_id: {resource: amount}}

        Returns:
            Dict of {agent_id: {resource: allocated_amount}}
        """
        logger.info(f"Starting resource negotiation for {len(agents)} agents")

        allocation = {}
        available_resources = {
            "cpu": 100.0,
            "memory_gb": 128.0,
            "gpu": 8,
        }

        # Try simple allocation first
        simple_allocation = self._simple_allocation(resource_needs, available_resources)
        if simple_allocation:
            logger.info("Simple allocation succeeded")
            return simple_allocation

        # Need negotiation
        logger.info("Initiating negotiation for constrained resources")
        negotiated = await self._iterative_negotiation(
            agents,
            resource_needs,
            available_resources
        )

        return negotiated

    # ==================== Conflict Resolution ====================

    async def resolve_agent_conflicts(self,
                                     conflicts: List[AgentConflict]) -> Dict[str, str]:
        """
        Resolve conflicts between agents.

        Strategies:
        1. Priority-based: Higher priority wins
        2. Time-based: Earlier request wins
        3. Consensus: Agents vote

        Args:
            conflicts: List of conflicts to resolve

        Returns:
            Dict of {conflict_id: resolution}
        """
        logger.info(f"Resolving {len(conflicts)} agent conflicts")

        resolutions = {}

        for conflict in conflicts:
            if conflict.conflict_type == "RESOURCE":
                resolution = self._resolve_resource_conflict(conflict)
            elif conflict.conflict_type == "SCHEDULING":
                resolution = self._resolve_scheduling_conflict(conflict)
            elif conflict.conflict_type == "STATE":
                resolution = self._resolve_state_conflict(conflict)
            else:
                resolution = "UNKNOWN_CONFLICT"

            resolutions[conflict.conflict_id] = resolution
            logger.info(f"Resolved conflict {conflict.conflict_id}: {resolution}")

        return resolutions

    # ==================== Collaboration Monitoring ====================

    async def get_collaboration_metrics(self,
                                       agents: List[AgentAggregate]) -> Dict:
        """
        Get metrics on collaboration effectiveness.

        Returns:
            Dict with collaboration statistics
        """
        total_agents = len(agents)
        available_agents = sum(1 for a in agents if a.is_available())
        busy_agents = sum(1 for a in agents if a.status == "BUSY")
        avg_success_rate = sum(a.get_success_rate() for a in agents) / total_agents if agents else 0

        return {
            "total_agents": total_agents,
            "available_agents": available_agents,
            "busy_agents": busy_agents,
            "utilization_percent": (busy_agents / total_agents * 100) if total_agents > 0 else 0,
            "average_success_rate": avg_success_rate,
            "health_check_pass_rate": sum(1 for a in agents if a.is_healthy()) / total_agents if agents else 0,
        }

    # ==================== Private Methods ====================

    def _topological_sort(self, dependencies: Dict[str, List[str]]) -> List[str]:
        """
        Topological sort of tasks based on dependencies.

        Ensures all dependencies execute before dependent tasks.

        Args:
            dependencies: Dict of {task_id: [dependency_ids]}

        Returns:
            List of task IDs in execution order
        """
        visited = set()
        stack = []

        def visit(node: str):
            if node in visited:
                return
            visited.add(node)

            for dependency in dependencies.get(node, []):
                visit(dependency)

            stack.append(node)

        for node in dependencies.keys():
            visit(node)

        return stack

    def _simple_allocation(self,
                          resource_needs: Dict[str, Dict],
                          available: Dict) -> Optional[Dict[str, Dict]]:
        """
        Try simple allocation without negotiation.

        Returns allocation if possible, None if resources insufficient.
        """
        total_needs = {}
        for agent_needs in resource_needs.values():
            for resource, amount in agent_needs.items():
                total_needs[resource] = total_needs.get(resource, 0) + amount

        # Check if we have enough
        for resource, amount in total_needs.items():
            if amount > available.get(resource, 0):
                return None

        # Allocation succeeds
        return resource_needs

    async def _iterative_negotiation(self,
                                     agents: List[AgentAggregate],
                                     requests: Dict[str, Dict],
                                     available: Dict,
                                     max_iterations: int = 3) -> Dict[str, Dict]:
        """
        Iterative negotiation for constrained resources.

        Agents reduce requests until agreement is reached.
        """
        current_requests = {agent_id: dict(req) for agent_id, req in requests.items()}

        for iteration in range(max_iterations):
            total_needed = {}
            for agent_needs in current_requests.values():
                for resource, amount in agent_needs.items():
                    total_needed[resource] = total_needed.get(resource, 0) + amount

            # Check if satisfied
            if all(total_needed.get(r, 0) <= available.get(r, 0) for r in total_needed):
                logger.info(f"Negotiation succeeded in iteration {iteration + 1}")
                return current_requests

            # Reduce requests
            for agent_id in current_requests:
                for resource in current_requests[agent_id]:
                    current_requests[agent_id][resource] *= 0.9  # Reduce by 10%

        # Return best effort allocation
        logger.warning("Negotiation did not fully resolve - returning best effort")
        return current_requests

    def _resolve_resource_conflict(self, conflict: AgentConflict) -> str:
        """Resolve resource contention - priority or fairness"""
        # Simple strategy: equal split
        return "EQUAL_DIVISION"

    def _resolve_scheduling_conflict(self, conflict: AgentConflict) -> str:
        """Resolve scheduling conflict - serialize or parallelize"""
        # Simple strategy: serialize (one then the other)
        return "SEQUENTIAL"

    def _resolve_state_conflict(self, conflict: AgentConflict) -> str:
        """Resolve state conflict - consistency"""
        # Simple strategy: most recent wins
        return "MOST_RECENT_WINS"
