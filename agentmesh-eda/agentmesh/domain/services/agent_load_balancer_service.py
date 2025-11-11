"""
Agent Load Balancer Domain Service

Architectural Intent:
- Encapsulates complex logic for selecting best agent for a task
- Uses domain concepts (capabilities, availability, performance)
- Returns agent selection based on multiple factors
- Supports different selection strategies

Key Design Decisions:
1. Service operates on aggregates (doesn't directly modify them)
2. Selection algorithm is deterministic and testable
3. Scoring mechanism is transparent (can be explained to users)
4. Supports custom weight configurations
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from agentmesh.domain.entities.agent_aggregate import AgentAggregate


@dataclass
class AgentScoreResult:
    """Result of agent scoring"""
    agent_id: str
    score: float  # 0.0-1.0
    breakdown: Dict[str, float]  # Score breakdown for debugging

    def __str__(self) -> str:
        factors = ", ".join([f"{k}={v:.2f}" for k, v in self.breakdown.items()])
        return f"Agent({self.agent_id}, score={self.score:.2f}, {factors})"


class AgentLoadBalancerService:
    """
    Domain Service: Select best agent for task.

    Algorithm factors:
    - Capability match (does agent have required skills?)
    - Availability (is agent ready for work?)
    - Current load (how busy is the agent?)
    - Performance (what's agent's success rate?)
    - Response time (how fast does agent respond?)

    Scoring formula:
    total_score = (capability_match * w_cap) +
                  (availability * w_avail) +
                  (inverse_load * w_load) +
                  (performance * w_perf) +
                  (inverse_response * w_response)

    Default weights: Capability (40%), Availability (25%), Load (15%), Performance (15%), Response (5%)
    """

    def __init__(self,
                 weights: Optional[Dict[str, float]] = None,
                 health_thresholds: Optional[Dict[str, float]] = None):
        """
        Initialize load balancer service.

        Args:
            weights: Custom scoring weights (must sum to 1.0)
            health_thresholds: Custom health check thresholds
        """
        # Default weights
        self.weights = weights or {
            "capability_match": 0.40,
            "availability": 0.25,
            "current_load": 0.15,
            "performance": 0.15,
            "response_time": 0.05,
        }

        # Validate weights sum to 1.0
        weight_sum = sum(self.weights.values())
        if abs(weight_sum - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")

        # Default health thresholds
        self.health_thresholds = health_thresholds or {
            "min_success_rate": 0.5,
            "max_error_rate": 0.2,
            "max_response_time_ms": 10000,
            "max_cpu_percent": 95,
            "max_memory_percent": 95,
        }

    def select_best_agent(self,
                         required_capabilities: List[str],
                         available_agents: List[AgentAggregate]) -> Optional[AgentAggregate]:
        """
        Select single best agent for task.

        Returns:
            Best matching agent, or None if no suitable agent found

        Raises:
            ValueError: If no agents provided or required capabilities list is empty
        """
        if not available_agents:
            return None
        if not required_capabilities:
            raise ValueError("Must specify required capabilities")

        # Score all agents
        scores = [
            self._score_agent(agent, required_capabilities)
            for agent in available_agents
        ]

        # Filter out agents that don't meet minimum requirements
        qualified_scores = [s for s in scores if self._is_qualified(s)]

        if not qualified_scores:
            return None

        # Return agent with highest score
        best_score = max(qualified_scores, key=lambda s: s.score)
        best_agent = next(a for a in available_agents if a.agent_id.value == best_score.agent_id)
        return best_agent

    def rank_agents(self,
                    required_capabilities: List[str],
                    available_agents: List[AgentAggregate]) -> List[AgentScoreResult]:
        """
        Rank all agents by suitability for task.

        Returns:
            List of AgentScoreResult sorted by score (highest first)

        Useful for:
        - Finding backup agents
        - Load distribution
        - Reporting on agent utilization
        """
        scores = [
            self._score_agent(agent, required_capabilities)
            for agent in available_agents
        ]
        return sorted(scores, key=lambda s: s.score, reverse=True)

    def select_multiple_agents(self,
                              required_capabilities: List[str],
                              available_agents: List[AgentAggregate],
                              count: int = 3,
                              min_score: float = 0.5) -> List[AgentAggregate]:
        """
        Select multiple agents for distributed task execution.

        Args:
            required_capabilities: Required agent capabilities
            available_agents: Pool of agents to choose from
            count: Number of agents to select
            min_score: Minimum score threshold (0.0-1.0)

        Returns:
            List of selected agents, sorted by score (highest first)
        """
        if count <= 0:
            raise ValueError("count must be positive")
        if not 0.0 <= min_score <= 1.0:
            raise ValueError("min_score must be 0.0-1.0")

        scores = self.rank_agents(required_capabilities, available_agents)

        # Filter by minimum score
        qualified = [s for s in scores if s.score >= min_score]

        # Select top N
        selected_scores = qualified[:count]
        selected_agents = [
            next(a for a in available_agents if a.agent_id.value == s.agent_id)
            for s in selected_scores
        ]

        return selected_agents

    # ==================== Private Methods ====================

    def _score_agent(self,
                    agent: AgentAggregate,
                    required_capabilities: List[str]) -> AgentScoreResult:
        """
        Score single agent for task.

        Returns AgentScoreResult with detailed breakdown.
        """
        breakdown = {}

        # 1. Capability match (can agent do the job?)
        capability_match = self._score_capability_match(agent, required_capabilities)
        breakdown["capability_match"] = capability_match

        # 2. Availability (is agent free?)
        availability = self._score_availability(agent)
        breakdown["availability"] = availability

        # 3. Current load (how busy?)
        load_score = 1.0 - agent.get_load()  # Inverse load (less load = higher score)
        breakdown["load"] = load_score

        # 4. Performance (success rate)
        performance = agent.get_success_rate()
        breakdown["performance"] = performance

        # 5. Response time (only if metrics available)
        response_score = 1.0
        if agent.current_metrics and agent.current_metrics.response_time_ms > 0:
            # Normalize to 0-1 scale (faster = higher score)
            max_response_time = 10000  # 10 seconds
            response_score = max(0.0, 1.0 - (agent.current_metrics.response_time_ms / max_response_time))
        breakdown["response_time"] = response_score

        # Calculate total score using weights
        total_score = (
            capability_match * self.weights["capability_match"] +
            availability * self.weights["availability"] +
            load_score * self.weights["current_load"] +
            performance * self.weights["performance"] +
            response_score * self.weights["response_time"]
        )

        return AgentScoreResult(
            agent_id=agent.agent_id.value,
            score=total_score,
            breakdown=breakdown
        )

    def _score_capability_match(self,
                                agent: AgentAggregate,
                                required_capabilities: List[str]) -> float:
        """
        Score how well agent matches required capabilities.

        Perfect match (all required + all at high level) = 1.0
        Partial match = 0.5
        No match = 0.0
        """
        if not required_capabilities:
            return 1.0

        matched = 0
        matched_proficiency = 0

        for required_cap in required_capabilities:
            capability = agent.get_capability(required_cap)
            if capability:
                matched += 1
                matched_proficiency += capability.proficiency_level

        # Base score: how many capabilities matched?
        match_ratio = matched / len(required_capabilities)

        # Proficiency boost: how skilled in those areas?
        if matched > 0:
            avg_proficiency = matched_proficiency / matched
            proficiency_ratio = avg_proficiency / 5.0  # Normalize to 0-1
        else:
            proficiency_ratio = 0.0

        # Combined score: 70% match, 30% proficiency
        return (match_ratio * 0.7) + (proficiency_ratio * 0.3)

    def _score_availability(self, agent: AgentAggregate) -> float:
        """
        Score agent availability.

        AVAILABLE = 1.0
        BUSY = 0.3 (can still be backup)
        PAUSED = 0.1
        UNHEALTHY/TERMINATED = 0.0
        """
        availability_scores = {
            "AVAILABLE": 1.0,
            "BUSY": 0.3,
            "PAUSED": 0.1,
            "UNHEALTHY": 0.0,
            "TERMINATED": 0.0,
        }
        return availability_scores.get(agent.status, 0.0)

    def _is_qualified(self, score: AgentScoreResult) -> bool:
        """
        Check if agent meets minimum qualification threshold.

        Must have:
        - At least 50% capability match
        - At least some availability (score > 0)
        """
        if score.score < 0.5:
            return False

        if score.breakdown.get("capability_match", 0.0) < 0.5:
            return False

        if score.breakdown.get("availability", 0.0) <= 0.0:
            return False

        return True
