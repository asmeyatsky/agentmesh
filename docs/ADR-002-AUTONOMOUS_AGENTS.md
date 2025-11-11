# ADR-002: Autonomous Agent Decision-Making

**Status**: Accepted
**Date**: October 29, 2024
**Context**: AgentMesh needs to scale beyond centralized orchestration

## Problem Statement

Centralized orchestrators become bottlenecks in large agent systems:
- Single point of failure
- Cannot scale to thousands of agents
- Slow decisions due to network latency
- Cannot support true decentralized systems

## Decision

Implement autonomous agents that:
1. Make own task acceptance decisions (via AgentAutonomyService)
2. Self-prioritize task queue
3. Monitor own health
4. Collaborate peer-to-peer with other agents
5. Publish events for system integration

## Rationale

### Why Autonomous Agents?

1. **Scalability**
   - No central bottleneck
   - Each agent independent
   - Horizontal scaling

2. **Resilience**
   - Failure of one agent doesn't stop system
   - Agents self-heal
   - Graceful degradation

3. **Responsiveness**
   - No orchestrator latency
   - Local decision-making
   - Real-time task acceptance

4. **True Distribution**
   - Agents coordinate peer-to-peer
   - Decentralized task assignment
   - Natural load balancing

### Decision Algorithm

**Task Acceptance Decision**:
1. Hard constraints (fail fast):
   - Agent available?
   - Agent healthy?
   - Agent has capabilities?
   - Agent success rate sufficient?

2. Soft constraints (scoring):
   - Task priority (40%)
   - Capability match (30%)
   - Agent workload (20%)
   - Deadline urgency (10%)

3. Accept if score ≥ threshold (0.6)

### Implementation

```python
# Agent receives task offering
decision = autonomy_service.should_accept_task(agent, task)

# Decision includes:
- should_accept: bool
- confidence: float (0.0-1.0)
- reason: str (human readable)
- factors: Dict (decision breakdown)

# Transparent and auditable
if decision.should_accept:
    agent = agent.assign_task(task.id)
    # Task added to agent's queue
else:
    # Task offered to other agents
```

## Consequences

### Positive
✅ Truly distributed architecture
✅ Scales to thousands of agents
✅ Resilient to failures
✅ Fast task acceptance decisions
✅ Agents can be heterogeneous

### Negative
⚠️ More complex coordination
⚠️ Potential for unbalanced load
⚠️ Need robust conflict resolution
⚠️ Consensus harder to achieve

## How It Works

### Scenario: 100 Tasks, 50 Agents

**Traditional (Centralized)**:
1. Orchestrator receives 100 tasks
2. Orchestrator makes 100 assignment decisions
3. Single point of failure
4. Bottleneck during high load

**Autonomous (Decentralized)**:
1. Tasks broadcast to all agents
2. Each agent independently decides if it can help
3. Most suitable agents self-select
4. Natural load distribution
5. Resilient to agent failures

## Integration with Other Systems

Events published for integration:
- `AgentTaskAssignedEvent` - Task accepted
- `AgentTaskCompletedEvent` - Task finished
- `AgentHealthCheckPassedEvent` - Agent healthy
- `AgentHealthCheckFailedEvent` - Agent unhealthy

Other systems react via event bus (no tight coupling).

## Related Decisions

- ADR-001: Domain-Driven Design
- ADR-003: Event-Driven Architecture
- ADR-005: Multi-Agent Collaboration

## Implementation Status

✅ AgentAutonomyService - Decision logic
✅ AutonomousAgent - Decision-making agent
✅ Decision auditing via events
⏳ Distributed consensus mechanisms
⏳ Multi-agent resource negotiation
