# ADR-003: Event-Driven Architecture for Integration

**Status**: Accepted
**Date**: October 29, 2024
**Context**: AgentMesh needs to integrate with multiple external systems while maintaining loose coupling

## Problem Statement

Tight coupling to external systems creates:
- Dependencies between components
- Hard to add new integrations
- Cascading failures
- Testing nightmare

## Decision

Adopt event-driven architecture:

1. **Domain Events** - Published when state changes in domain
2. **Event Bus** - Central hub for event distribution
3. **Event Subscribers** - Systems react to events
4. **Loose Coupling** - No direct dependencies between systems

## Rationale

### Why Events?

1. **Loose Coupling**
   - Agent doesn't know about external systems
   - External systems subscribe to events
   - Easy to add/remove integrations

2. **Auditability**
   - Complete record of what happened
   - Event sourcing enables time travel
   - Compliance and debugging

3. **Scalability**
   - Systems can process events asynchronously
   - Non-blocking operations
   - High throughput

4. **Extensibility**
   - New integrations without changing agent code
   - Event subscribers are independent
   - Easy to test event handlers

### Implementation

**13 Domain Events** published by AgentAggregate:

```python
# When agent created
AgentCreatedEvent(agent_id, tenant_id, capabilities, ...)

# When task assigned
AgentTaskAssignedEvent(agent_id, task_id, assigned_at)

# When task completed
AgentTaskCompletedEvent(agent_id, task_id, result, execution_time_ms)

# When task failed
AgentTaskFailedEvent(agent_id, task_id, error_message, error_code)

# When health check passed
AgentHealthCheckPassedEvent(agent_id, metrics...)

# When health check failed
AgentHealthCheckFailedEvent(agent_id, reason, last_seen)

# ... 7 more events
```

### Event Publishing Flow

```
Domain Operation
    ↓
AgentAggregate method (e.g., complete_task())
    ↓
Event created (e.g., AgentTaskCompletedEvent)
    ↓
Event published via EventBus
    ↓
Event subscribers react:
    - Update read models
    - Trigger notifications
    - Update external systems
    - Log to audit trail
```

## Consequences

### Positive
✅ Decoupled systems
✅ Easy to add integrations
✅ Complete audit trail
✅ Event sourcing enabled
✅ Supports future analytics/ML

### Negative
⚠️ Eventual consistency (not immediate)
⚠️ Need robust event handling
⚠️ Debugging distributed systems harder
⚠️ Event versioning needed over time

## Integration Points

### Example: Monitoring System

```python
# Monitoring subscribes to health events
event_bus.subscribe("AgentHealthCheckFailedEvent", handle_unhealthy_agent)

# When agent fails health check:
# 1. AgentHealthCheckFailedEvent published
# 2. Monitoring handler called
# 3. Alert sent
# 4. Dashboard updated
# 5. All without agent knowing about monitoring
```

### Example: Analytics System

```python
# Analytics subscribes to task completion events
event_bus.subscribe("AgentTaskCompletedEvent", record_task_metrics)

# When task completed:
# 1. AgentTaskCompletedEvent published
# 2. Analytics records execution time
# 3. Dashboard shows completion rate
# 4. Trends analyzed
```

## Event Sourcing

With these events, we can:

1. **Reconstruct agent state**
   - Replay events to rebuild state
   - Time travel to any point in past
   - No need for snapshots (initially)

2. **Complete audit trail**
   - Every state change is event
   - Who did what, when
   - Compliance ready

3. **Offline processing**
   - Events can be processed later
   - Systems can be temporarily offline
   - Eventual consistency achieved

## Related Decisions

- ADR-001: Domain-Driven Design
- ADR-004: Ports & Adapters Pattern
- ADR-002: Autonomous Agents

## Event Versioning Strategy

For future compatibility:
```python
@dataclass(frozen=True)
class DomainEvent:
    aggregate_id: str
    occurred_at: datetime
    version: str = "1.0"  # Event version
```

If event structure changes in future:
- Old subscribers still work (v1.0 handlers)
- New subscribers use v2.0
- Gradual migration path

## Implementation Status

✅ 13 domain events defined
✅ Event publishing via CreateAgentUseCase
✅ InMemoryEventBus for testing
⏳ Persistent event store
⏳ Event subscribers/handlers
⏳ Event schema registry
