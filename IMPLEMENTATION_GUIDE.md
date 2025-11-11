# AgentMesh Implementation Guide

## Quick Start

This guide helps developers understand and work with the refactored AgentMesh architecture.

---

## Prerequisites

Before starting, read these in order:
1. `claude.md` - Architectural principles and rules
2. `ARCHITECTURE_REFACTORING.md` - Detailed refactoring plan
3. `REFACTORING_PROGRESS.md` - Current status and completed work
4. `SECURITY_SETUP.md` - Security configuration

---

## Setting Up Development Environment

### 1. Clone and Setup

```bash
cd /Users/allansmeyatsky/agentmesh/agentmesh-eda

# Copy environment file
cp .env.example .env

# Generate encryption key
ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Generate JWT secret
JWT_SECRET=$(openssl rand -hex 32)

# Update .env with values
cat > .env << EOF
ENCRYPTION_KEY=$ENCRYPTION_KEY
JWT_SECRET_KEY=$JWT_SECRET
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
DATABASE_URL=postgresql://agentmesh:agentmesh@localhost:5432/agentmesh
NATS_URL=nats://localhost:4222
ENVIRONMENT=development
LOG_LEVEL=INFO
EOF
```

### 2. Start Services

```bash
# Start Docker Compose (PostgreSQL, NATS, etc.)
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 3. Run Existing Tests

```bash
# Install dependencies
poetry install

# Run tests
pytest -v

# Run with coverage
pytest --cov=agentmesh tests/
```

---

## Architecture Overview

### Layered Architecture

```
┌─────────────────────────────────────────┐
│    Presentation Layer (CLI, Web, API)   │
├─────────────────────────────────────────┤
│   Application Layer (Use Cases, DTOs)   │
├─────────────────────────────────────────┤
│  Domain Layer (Aggregates, Services)    │
├─────────────────────────────────────────┤
│Infrastructure (Database, Adapters, Ext) │
└─────────────────────────────────────────┘
```

### Ports & Adapters Pattern

```
Domain (Interfaces):          Infrastructure (Implementations):
  └─ MessagePersistencePort  ────→  PostgresMessagePersistenceAdapter
  └─ TenantRepositoryPort    ────→  PostgresTenantAdapter
  └─ MessageBrokerPort       ────→  NatsAdapter, KafkaAdapter, etc.
  └─ AgentRepositoryPort     ────→  PostgresAgentAdapter
```

---

## Working With the Code

### Adding a New Feature

Follow this flow (from `claude.md`):

#### Step 1: Define Port Interface

```python
# agentmesh/domain/ports/my_feature_port.py

from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass(frozen=True)
class MyFeatureResult:
    """Result of my feature operation"""
    id: str
    status: str

class MyFeaturePort(ABC):
    """Port: Description of what this does"""

    @abstractmethod
    async def do_something(self, data: dict) -> MyFeatureResult:
        """Do something and return result"""
        pass
```

#### Step 2: Create Domain Models

```python
# agentmesh/domain/entities/my_feature.py

from dataclasses import dataclass

@dataclass(frozen=True)
class MyFeature:
    """
    Immutable domain model.

    Invariants:
    - id must be non-empty
    - status must be valid enum
    """
    id: str
    status: str

    def __post_init__(self):
        if not self.id:
            raise ValueError("id cannot be empty")
```

#### Step 3: Create Domain Service

```python
# agentmesh/domain/services/my_feature_service.py

from agentmesh.domain.entities.my_feature import MyFeature

class MyFeatureDomainService:
    """Domain service: Orchestrates complex feature logic"""

    def validate_feature(self, feature: MyFeature) -> bool:
        """Business logic for feature validation"""
        return feature.id and feature.status
```

#### Step 4: Implement Adapter

```python
# agentmesh/infrastructure/adapters/my_feature_adapter.py

from agentmesh.domain.ports.my_feature_port import MyFeaturePort, MyFeatureResult

class MyFeatureAdapter(MyFeaturePort):
    """Concrete implementation of MyFeaturePort"""

    async def do_something(self, data: dict) -> MyFeatureResult:
        # Actual implementation
        return MyFeatureResult(id="123", status="success")
```

#### Step 5: Create Use Case

```python
# agentmesh/application/use_cases/my_feature_use_case.py

from dataclasses import dataclass
from agentmesh.domain.ports.my_feature_port import MyFeaturePort

@dataclass
class MyFeatureDTO:
    data: dict

class MyFeatureUseCase:
    """Use Case: Orchestrate domain objects"""

    def __init__(self, port: MyFeaturePort):
        self.port = port

    async def execute(self, dto: MyFeatureDTO):
        return await self.port.do_something(dto.data)
```

#### Step 6: Write Tests

```python
# tests/unit/domain/entities/test_my_feature.py

import pytest
from agentmesh.domain.entities.my_feature import MyFeature

def test_my_feature_creation():
    feature = MyFeature(id="123", status="active")
    assert feature.id == "123"

def test_my_feature_requires_id():
    with pytest.raises(ValueError):
        MyFeature(id="", status="active")
```

---

## Common Tasks

### Adding a Messaging Adapter

```python
# agentmesh/mal/adapters/my_broker.py

from agentmesh.mal.adapters.base import MessagePlatformAdapter
from agentmesh.mal.message import UniversalMessage

class MyBrokerAdapter(MessagePlatformAdapter):
    async def send(self, message: UniversalMessage, topic: str):
        # Serialize and send to your broker
        payload = message.serialize()
        # Send implementation...
```

### Adding a Repository Implementation

```python
# agentmesh/infrastructure/adapters/postgres_agent_adapter.py

from agentmesh.domain.ports.agent_port import AgentRepositoryPort

class PostgresAgentAdapter(AgentRepositoryPort):
    async def save(self, agent: AgentAggregate) -> None:
        # Convert aggregate to ORM model
        # Save to database
        pass

    async def get_by_id(self, agent_id: str, tenant_id: str) -> Optional[AgentAggregate]:
        # Query database
        # Convert ORM model back to aggregate
        pass
```

### Creating a Domain Event

```python
# agentmesh/domain/domain_events/my_events.py

from dataclasses import dataclass
from agentmesh.cqrs.event import DomainEvent

@dataclass(frozen=True)
class MyFeatureCreatedEvent(DomainEvent):
    """Event: MyFeature was created"""
    feature_id: str
    created_at: datetime

    # Publish in use case or aggregate method
    # event = MyFeatureCreatedEvent(...)
    # await event_bus.publish(event)
```

---

## Testing

### Unit Testing (Domain Logic)

```python
# tests/unit/domain/entities/test_agent_aggregate.py

import pytest
from agentmesh.domain.entities.agent_aggregate import AgentAggregate

def test_agent_state_transitions():
    agent = AgentAggregate(...)

    # Test transition
    busy = agent.assign_task()
    assert busy.status == "BUSY"

    # Test immutability
    assert agent.status == "AVAILABLE"  # Original unchanged
```

### Integration Testing (Use Cases)

```python
# tests/integration/application/test_my_use_case.py

import pytest
from agentmesh.application.use_cases.my_use_case import MyUseCase
from agentmesh.infrastructure.adapters.mock_adapter import MockAdapter

@pytest.mark.asyncio
async def test_use_case_execution():
    adapter = MockAdapter()
    use_case = MyUseCase(adapter)

    result = await use_case.execute(...)

    assert result.status == "success"
```

### End-to-End Testing

```python
# tests/e2e/test_message_routing.py

@pytest.mark.asyncio
async def test_message_routing_workflow():
    # Setup full system
    router = setup_router()
    message = create_test_message()

    # Execute workflow
    await router.route_message(message)

    # Verify results
    assert message_was_delivered()
```

---

## Security Checklist

When implementing features:

- [ ] No hardcoded secrets (use environment variables)
- [ ] All external dependencies behind port interfaces
- [ ] Tenant ID validated on every operation
- [ ] Authentication token verified
- [ ] Authorization checked against roles
- [ ] Encryption used for sensitive data
- [ ] Logging includes audit trail
- [ ] Error messages don't expose internal details
- [ ] Input validation on all boundaries
- [ ] Tests verify security constraints

---

## Performance Considerations

### Database Queries
- Create indexes on `tenant_id`, `agent_id`, `message_type`
- Use pagination for large result sets
- Consider caching for read-heavy operations

### Message Routing
- Use load balancing to distribute across adapters
- Consider async processing for slow operations
- Implement rate limiting per tenant

### Encryption
- Encryption has minimal overhead (~5%)
- Consider bulk encryption for batch operations
- Cache cipher instances to avoid repeated initialization

---

## Common Mistakes to Avoid

### ❌ Anti-Patterns

```python
# WRONG: Business logic in repository
class UserRepository:
    def get_premium_users(self):
        users = self.db.query(User)
        return [u for u in users if u.premium]  # Logic here!

# RIGHT: Logic in domain service
class UserDomainService:
    def get_premium_users(self, repo, users):
        return [u for u in users if self._is_premium(u)]

# WRONG: Direct database access in service
class MyService:
    def process(self, data):
        db.query(...)  # Tight coupling!

# RIGHT: Use port interface
class MyService:
    def __init__(self, port: MyPort):
        self.port = port

    async def process(self, data):
        return await self.port.do_something(data)

# WRONG: Mutable domain models
class Agent:
    def assign_task(self):
        self.status = "BUSY"  # Mutation!

# RIGHT: Immutable models
@dataclass(frozen=True)
class Agent:
    def assign_task(self) -> 'Agent':
        return replace(self, status="BUSY")  # New instance
```

---

## Debugging

### Enable Debug Logging

```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG

# Or temporarily in code
from loguru import logger
logger.enable("agentmesh")
```

### Check Configuration

```python
from agentmesh.security.config import get_security_config

config = get_security_config()
print(f"Encryption key: {config.encryption_key[:20]}...")
print(f"JWT algorithm: {config.jwt_algorithm}")
```

### Inspect Messages

```python
from agentmesh.mal.message import UniversalMessage

message = UniversalMessage(...)
print(message.serialize())  # Pretty-print as JSON
```

### Test Database

```bash
# Connect to PostgreSQL
psql -U agentmesh -d agentmesh

# Check message table
SELECT id, tenant_id, message_type, persisted_at
FROM message
LIMIT 10;
```

---

## Deployment

### Docker Compose (Development)

```bash
docker-compose up -d
docker-compose logs -f agentmesh
```

### Kubernetes (Future)

Configuration prepared via 12-factor app principles:
- Environment-based configuration
- Stateless services
- Graceful shutdown handling

---

## Documentation Standards

All new code must include:

```python
"""
Module Description

Architectural Intent:
- Purpose and responsibility
- Design decisions
- Key features

Key Design Decisions:
1. Why we chose this approach
2. Trade-offs made
3. Performance considerations
"""
```

---

## Getting Help

1. **Questions about architecture?** → Read `claude.md`
2. **Implementation details?** → Check `ARCHITECTURE_REFACTORING.md`
3. **Security issues?** → See `SECURITY_SETUP.md`
4. **Current progress?** → Review `REFACTORING_PROGRESS.md`

---

## Contributing

### Code Style

```python
# Follow PEP 8
# Use type hints
def my_function(param: str) -> bool:
    """Use docstrings for all functions"""
    return True

# Use dataclasses for immutable models
@dataclass(frozen=True)
class MyModel:
    field: str
```

### Commit Message Format

```
feat: Add new feature following DDD principles

- Implemented AgentAggregate with immutable state
- Created AgentRepositoryPort interface
- Added comprehensive tests

Closes #123
```

### PR Checklist

- [ ] Follows architectural guidelines from claude.md
- [ ] New code is behind port interfaces
- [ ] Tests cover domain logic
- [ ] Documentation includes architectural intent
- [ ] No hardcoded secrets or configuration
- [ ] Security checklist completed
- [ ] Performance impact assessed

---

## Useful Commands

```bash
# Run tests
pytest -v

# Run with coverage
pytest --cov=agentmesh tests/

# Type checking
mypy agentmesh/

# Code formatting
black agentmesh/

# Linting
ruff check agentmesh/

# View logs
docker-compose logs -f agentmesh

# Database shell
psql -U agentmesh -d agentmesh
```

---

**Last Updated**: October 29, 2024
**Status**: Ready for Development
