"""
Agent Autonomy Domain Service

Architectural Intent:
- Encapsulates logic for autonomous agent decision making
- Agents decide whether to accept/reject tasks independently
- Respects agent constraints and preferences
- Enables distributed task assignment without central bottleneck

Key Design Decisions:
1. Service provides decision logic, doesn't modify agents
2. Decisions are transparent (can be explained)
3. Supports multi-factor decision trees
4. Agents can have different autonomy levels

Decision Factors:
- Agent has required capabilities?
- Agent has capacity (not overloaded)?
- Task priority vs agent preference
- Agent recent performance
- Agent resource availability
- System load and urgency
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from agentmesh.domain.entities.agent_aggregate import AgentAggregate


@dataclass
class TaskOffering:
    """Offered task for agent to consider"""
    task_id: str
    required_capabilities: List[str]
    priority: int  # 1-5, where 5 is highest
    estimated_duration_seconds: int
    estimated_resource_load: float  # 0.0-1.0
    deadline: Optional[int] = None  # Seconds from now
    required_success_rate: float = 0.7  # Min success rate to accept


@dataclass
class DecisionResult:
    """Result of autonomy decision"""
    should_accept: bool
    confidence: float  # 0.0-1.0, how confident is decision?
    reason: str  # Human-readable explanation
    factors: Dict[str, bool]  # Breakdown of decision factors


class AgentAutonomyService:
    """
    Domain Service: Autonomous agent decision making.

    Enables agents to independently decide which tasks to accept.
    Reduces load on centralized orchestrator.
    Improves system responsiveness.

    Decision Process:
    1. Check hard constraints (capabilities, health)
    2. Check soft constraints (load, performance)
    3. Score task attractiveness
    4. Accept if score exceeds threshold
    """

    def __init__(self,
                 accept_threshold: float = 0.6,
                 max_concurrent_tasks: int = 5):
        """
        Initialize autonomy service.

        Args:
            accept_threshold: Score threshold for accepting tasks (0.0-1.0)
            max_concurrent_tasks: Maximum tasks agent handles simultaneously
        """
        if not 0.0 <= accept_threshold <= 1.0:
            raise ValueError("accept_threshold must be 0.0-1.0")
        if max_concurrent_tasks <= 0:
            raise ValueError("max_concurrent_tasks must be positive")

        self.accept_threshold = accept_threshold
        self.max_concurrent_tasks = max_concurrent_tasks

    def should_accept_task(self,
                          agent: AgentAggregate,
                          task: TaskOffering) -> DecisionResult:
        """
        Decide if agent should accept offered task.

        Decision process:
        1. Hard constraints: If any fails, reject immediately
        2. Soft constraints: Used for scoring
        3. Score and compare to threshold

        Args:
            agent: Agent considering the task
            task: Task being offered

        Returns:
            DecisionResult with decision and reasoning
        """
        factors = {}

        # === HARD CONSTRAINTS ===
        # If any of these fail, reject immediately

        # 1. Agent must be available
        if not agent.is_available():
            return DecisionResult(
                should_accept=False,
                confidence=1.0,
                reason=f"Agent is {agent.status}, not available for new tasks",
                factors={"available": False}
            )

        # 2. Agent must be healthy
        if not agent.is_healthy():
            return DecisionResult(
                should_accept=False,
                confidence=1.0,
                reason="Agent health check failed",
                factors={"healthy": False}
            )

        # 3. Agent must have all required capabilities
        if not agent.has_all_capabilities(task.required_capabilities):
            missing = [c for c in task.required_capabilities if not agent.has_capability(c)]
            return DecisionResult(
                should_accept=False,
                confidence=1.0,
                reason=f"Agent missing required capabilities: {missing}",
                factors={"has_capabilities": False}
            )

        # 4. Agent must meet required success rate
        if agent.get_success_rate() < task.required_success_rate:
            return DecisionResult(
                should_accept=False,
                confidence=1.0,
                reason=f"Agent success rate {agent.get_success_rate():.1%} < required {task.required_success_rate:.1%}",
                factors={"meets_success_rate": False}
            )

        # All hard constraints passed
        factors["available"] = True
        factors["healthy"] = True
        factors["has_capabilities"] = True
        factors["meets_success_rate"] = True

        # === SOFT CONSTRAINTS ===
        # Used for scoring and prioritization

        score = self._score_task_attractiveness(agent, task, factors)

        if score < self.accept_threshold:
            return DecisionResult(
                should_accept=False,
                confidence=score,
                reason=f"Task attractiveness score {score:.2f} below threshold {self.accept_threshold}",
                factors=factors
            )

        return DecisionResult(
            should_accept=True,
            confidence=score,
            reason=f"Task accepted (score: {score:.2f})",
            factors=factors
        )

    def prioritize_tasks(self,
                        agent: AgentAggregate,
                        task_offerings: List[TaskOffering]) -> List[TaskOffering]:
        """
        Prioritize multiple task offerings for agent.

        Returns tasks sorted by attractiveness score (highest first).
        Agent should work through list in order.

        Args:
            agent: Agent considering multiple tasks
            task_offerings: List of available tasks

        Returns:
            Sorted list of tasks by attractiveness
        """
        scored_tasks = []

        for task in task_offerings:
            # Skip tasks agent can't do
            if not agent.has_all_capabilities(task.required_capabilities):
                continue

            factors = {}
            score = self._score_task_attractiveness(agent, task, factors)
            scored_tasks.append((score, task))

        # Sort by score (highest first)
        scored_tasks.sort(key=lambda x: x[0], reverse=True)
        return [task for _, task in scored_tasks]

    def get_agent_workload(self, agent: AgentAggregate) -> float:
        """
        Estimate agent's current workload (0.0-1.0).

        Factors:
        - Current task status
        - Number of tasks assigned
        - Task complexity
        - Recent CPU/memory usage
        """
        # Base load from status
        load = agent.get_load()

        # Add load from task count
        task_load = min(1.0, (agent.tasks_assigned / self.max_concurrent_tasks))
        load = (load + task_load) / 2.0

        # Adjust by metrics if available
        if agent.current_metrics:
            metrics_load = (
                (agent.current_metrics.cpu_usage_percent / 100.0 * 0.5) +
                (agent.current_metrics.memory_usage_percent / 100.0 * 0.5)
            )
            load = (load + metrics_load) / 2.0

        return min(1.0, load)

    def should_pause_for_maintenance(self, agent: AgentAggregate) -> bool:
        """
        Decide if agent should pause for maintenance.

        Triggers:
        - Error rate too high (learning opportunity)
        - Performance degrading (might need update)
        - Resource constraints detected
        """
        # High error rate indicates issues
        if agent.tasks_failed > 0:
            error_rate = agent.tasks_failed / (agent.tasks_completed + agent.tasks_failed)
            if error_rate > 0.3:
                return True

        # Degrading performance
        if agent.current_metrics:
            if agent.current_metrics.success_rate < 0.5:
                return True

        return False

    # ==================== Private Methods ====================

    def _score_task_attractiveness(self,
                                   agent: AgentAggregate,
                                   task: TaskOffering,
                                   factors: Dict[str, bool]) -> float:
        """
        Score how attractive task is for agent.

        Scoring factors:
        - Priority (higher priority = more attractive) - 40%
        - Capability match (how skilled?) - 30%
        - Agent workload (do they have capacity?) - 20%
        - Deadline pressure (urgent vs relaxed) - 10%

        Returns score 0.0-1.0
        """
        # 1. Priority factor (40%)
        priority_score = task.priority / 5.0
        priority_factor = priority_score * 0.40

        # 2. Capability match (30%)
        capability_scores = []
        for cap_name in task.required_capabilities:
            cap = agent.get_capability(cap_name)
            if cap:
                # Proficiency bonus: expert agents prefer matching tasks
                proficiency_score = cap.proficiency_level / 5.0
                capability_scores.append(proficiency_score)

        avg_capability = sum(capability_scores) / len(capability_scores) if capability_scores else 0.0
        capability_factor = avg_capability * 0.30

        # 3. Workload (20%)
        workload = self.get_agent_workload(agent)
        workload_score = 1.0 - min(workload, 1.0)  # Lower workload = higher score
        workload_factor = workload_score * 0.20

        # 4. Deadline (10%)
        deadline_score = 1.0  # Default: no deadline pressure
        if task.deadline:
            deadline_hours = task.deadline / 3600.0
            # Score decreases with tight deadline (1 hour = 0.5, more = 1.0)
            deadline_score = min(1.0, deadline_hours / 2.0)
        deadline_factor = deadline_score * 0.10

        total_score = priority_factor + capability_factor + workload_factor + deadline_factor

        # Store breakdown in factors dict
        factors["priority_score"] = True if priority_score > 0.3 else False
        factors["has_capacity"] = True if workload_score > 0.3 else False

        return min(1.0, total_score)
