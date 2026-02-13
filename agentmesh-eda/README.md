# AgentMesh EDA

**Enterprise-grade framework for building autonomous, self-organizing multi-agent AI systems with event-driven architecture.**

AgentMesh EDA provides unified abstractions over multiple messaging platforms, autonomous agent coordination, enterprise security, and production resilience patterns — so teams can focus on AI capabilities instead of infrastructure.

---

## Table of Contents

- [Architecture](#architecture)
- [Key Capabilities](#key-capabilities)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [CLI Reference](#cli-reference)
- [REST API](#rest-api)
- [WebSocket API](#websocket-api)
- [Agent Types](#agent-types)
- [Coordination Patterns](#coordination-patterns)
- [Message Abstraction Layer](#message-abstraction-layer)
- [Domain Model](#domain-model)
- [Security](#security)
- [Resilience Patterns](#resilience-patterns)
- [Observability](#observability)
- [Web UI](#web-ui)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)

---

## Architecture

AgentMesh EDA is built on a layered architecture following Domain-Driven Design, Clean Architecture, and CQRS principles.

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│           FastAPI REST  ·  WebSocket  ·  CLI  ·  Web UI      │
├─────────────────────────────────────────────────────────────┤
│                     Application Layer                        │
│                  Use Cases  ·  DTOs  ·  CQRS                 │
├─────────────────────────────────────────────────────────────┤
│                      Domain Layer                            │
│   Aggregates · Value Objects · Domain Events · Services      │
├─────────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                       │
│    Repositories · Message Adapters · Encryption · Metrics    │
└──┬───────┬────────┬────────┬────────┬───────┬───────────────┘
   │       │        │        │        │       │
 NATS    Kafka   Pub/Sub  Pulsar  SNS/SQS  Vertex AI
```

### System Layers

| Layer | Purpose | Key Components |
|-------|---------|----------------|
| **MAL** (Message Abstraction Layer) | Platform-agnostic messaging | Universal message format, 7 broker adapters, intelligent routing |
| **AOL** (Agent Orchestration Layer) | Agent lifecycle and coordination | 10 agent types, registry, load balancing, swarm orchestration |
| **EPE** (Event Processing Engine) | Real-time event analysis | Stream processing, anomaly detection |
| **GOL** (Governance & Observability) | Monitoring and governance | Metrics, audit logging, health checks |
| **ICL** (Integration & Connectivity) | External system integration | API gateway, connectors |

```mermaid
graph TD
    subgraph AgentMesh EDA Platform
        MAL[Message Abstraction Layer] --> AOL[Agent Orchestration Layer]
        AOL --> EPE[Event Processing Engine]
        EPE --> GOL[Governance & Observability Layer]
        ICL[Integration & Connectivity Layer] --> MAL
        MAL --> ICL
    end

    subgraph External Systems
        MP[Messaging Platforms]
        AIML[AI/ML Integration]
        DPS[Data Processing & Storage]
    end

    MP -- Events/Commands --> MAL
    MAL -- Events/Commands --> MP
    EPE -- Data --> DPS
    DPS -- Data --> EPE
    AOL -- Agent Models/Data --> AIML
    AIML -- Agent Models/Data --> AOL
    GOL -- Metrics/Logs --> OT(Observability Tools)
```

---

## Key Capabilities

- **Multi-platform messaging** — Single message format across NATS, Kafka, Pub/Sub, Pulsar, SNS/SQS, Vertex AI
- **Autonomous agents** — Self-organizing task acceptance, prioritization, and workload management
- **5 coordination patterns** — Orchestrator-worker, hierarchical, blackboard, market-based, swarm intelligence
- **Enterprise security** — JWT auth, Fernet encryption, tenant isolation, RBAC, audit logging
- **Resilience** — Circuit breaker, bulkhead isolation, retry with exponential backoff
- **Observability** — 25+ Prometheus metrics, anomaly detection, structured logging
- **CQRS + Event Sourcing** — 14 domain events, command/query separation, event store
- **Real-time streaming** — WebSocket support for live agent status and task updates
- **Safety & alignment** — Pre-execution validation, alignment scoring, agent quarantine
- **Federated learning** — Distributed model training with privacy preservation
- **Multi-tenancy** — Full tenant isolation across all operations

---

## Quick Start

### Prerequisites

- **Docker** and **Docker Compose**
- **Python 3.9+** (for local development)

### Run with Docker

```bash
git clone <repository_url>
cd agentmesh-eda

# Start all services (app + NATS + PostgreSQL)
docker-compose up --build -d

# Verify services are running
docker-compose ps
```

This starts:
- **agentmesh** — Main application container
- **nats** — NATS messaging server (ports 4222, 8222)
- **postgres** — PostgreSQL 13 database (port 5432)
- **api_gateway** — FastAPI API gateway (port 8000)

### Local Development

```bash
# Install Poetry
pip install poetry

# Install dependencies
poetry install

# Set required environment variables
export ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
export JWT_SECRET_KEY=$(openssl rand -hex 32)

# Run tests
poetry run pytest

# Start the API server
poetry run uvicorn agentmesh.api.fastapi_app:app --host 0.0.0.0 --port 8000
```

### Create Your First Agent

```bash
# Create a tenant
docker-compose exec agentmesh python -m agentmesh.cli.main tenant create mytenant

# Start a simple agent
docker-compose exec -d agentmesh python -m agentmesh.cli.main agent start agent-1 \
  --capabilities "data-processing"

# Check system status
docker-compose exec agentmesh python -m agentmesh.cli.main status
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENCRYPTION_KEY` | Yes | — | Fernet encryption key (44 bytes, base64). Generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `JWT_SECRET_KEY` | Yes | — | JWT signing key. Generate: `openssl rand -hex 32` |
| `JWT_ALGORITHM` | No | `HS256` | JWT algorithm (`HS256`, `HS384`, `HS512`, `RS256`) |
| `JWT_EXPIRATION_HOURS` | No | `24` | Token expiration in hours |
| `DATABASE_URL` | No | `postgresql://user:password@postgres/agentmesh_db` | PostgreSQL connection string |
| `NATS_URL` | No | `nats://localhost:4222` | NATS server URL |
| `KAFKA_BROKERS` | No | `localhost:9092` | Kafka bootstrap servers (comma-separated) |
| `GCP_PROJECT_ID` | No | — | Google Cloud project ID |
| `GOOGLE_APPLICATION_CREDENTIALS` | No | — | Path to GCP service account JSON |
| `VERTEX_AI_MODEL` | No | `gemini-1.5-pro` | Vertex AI model name |
| `PUBSUB_EMULATOR_HOST` | No | — | Pub/Sub emulator host for local dev |
| `ENVIRONMENT` | No | `development` | Environment level (`development`, `staging`, `production`) |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `API_HOST` | No | `0.0.0.0` | API bind host |
| `API_PORT` | No | `8000` | API bind port |
| `PROMETHEUS_ENABLED` | No | `true` | Enable Prometheus metrics |
| `PROMETHEUS_PORT` | No | `9090` | Prometheus metrics port |

---

## CLI Reference

```bash
python -m agentmesh.cli.main <command>
```

### Tenant Management

```bash
# Create a tenant
tenant create <name>

# List all tenants
tenant list
```

### System

```bash
# View system status
status

# View a message by ID
message view <message_id>
```

### Agent Lifecycle

| Command | Description | Key Options |
|---------|-------------|-------------|
| `agent start <id>` | Start a SimpleAgent | `--capabilities` |
| `agent start-task-executor <id>` | Start a TaskExecutorAgent | `--capabilities` |
| `agent start-orchestrator <id>` | Start an OrchestratorAgent | `--capabilities`, `--tenant-id`, `--target-agent-id`, `--task-details` |
| `agent start-kafka-agent <id>` | Start a KafkaAgent | `--capabilities` |
| `agent start-vertex-agent <id>` | Start a VertexAIAgent | `--capabilities`, `--gcp-project-id`, `--model-name` |
| `agent start-swarm-orchestrator <id>` | Start a SwarmOrchestrator | `--capabilities` |
| `agent start-swarm-worker <id>` | Start a SwarmWorkerAgent | `--capabilities`, `--swarm-orchestrator-id` |
| `agent start-federated-agent <id>` | Start a FederatedLearningAgent | `--capabilities` |
| `agent start-safety-agent <id>` | Start a SafetyAwareAgent | `--capabilities`, `--agent-type` |
| `agent start-decentralized-agent <id>` | Start a DecentralizedAgent | `--capabilities`, `--cluster-nodes` |

### Examples

```bash
# Start a swarm with orchestrator and workers
agent start-swarm-orchestrator swarm-1 --capabilities "coordination,management"
agent start-swarm-worker worker-1 --capabilities "processing" --swarm-orchestrator-id swarm-1
agent start-swarm-worker worker-2 --capabilities "analysis" --swarm-orchestrator-id swarm-1

# Start a Vertex AI agent with Gemini
agent start-vertex-agent ai-agent-1 \
  --capabilities "reasoning,generation" \
  --gcp-project-id my-project \
  --model-name gemini-1.5-pro

# Start decentralized agents with Raft consensus
agent start-decentralized-agent node-1 \
  --capabilities "consensus,coordination" \
  --cluster-nodes node-2 node-3 node-4
```

---

## REST API

Base URL: `http://localhost:8000`

Interactive documentation available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

### Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | No | Health check — returns status, uptime, version |
| `GET` | `/v1/tenants/{tenant_id}/agents` | Bearer | List all agents for a tenant |
| `POST` | `/v1/tenants/{tenant_id}/agents` | Bearer | Create a new agent |
| `GET` | `/v1/tenants/{tenant_id}/agents/{agent_id}` | Bearer | Get agent by ID |
| `GET` | `/v1/metrics` | No | System metrics — agent count, throughput, uptime |
| `GET` | `/docs` | No | Swagger UI documentation |
| `GET` | `/redoc` | No | ReDoc documentation |
| `GET` | `/openapi.json` | No | OpenAPI 3.0 schema |

### Authentication

All protected endpoints require a Bearer token in the `Authorization` header:

```bash
curl -H "Authorization: Bearer <jwt_token>" \
  http://localhost:8000/v1/tenants/my-tenant/agents
```

### Create Agent Request

```json
POST /v1/tenants/my-tenant/agents
{
  "agent_id": "processor-1",
  "name": "Data Processor",
  "agent_type": "processor",
  "description": "Processes incoming data streams",
  "capabilities": [
    {"name": "data_processing", "level": 4.0},
    {"name": "analysis", "level": 3.0}
  ],
  "metadata": {"team": "data-engineering"},
  "tags": ["production", "data-pipeline"]
}
```

### Validation Rules

| Field | Constraint |
|-------|-----------|
| `tenant_id` | 3–64 characters, alphanumeric + hyphens/underscores |
| `agent_id` | 3–256 characters, alphanumeric + hyphens/underscores |
| `name` | 3–256 characters |
| `description` | Max 1000 characters |
| `capabilities` | At least 1 required; level 1.0–5.0 |
| `tags` | Max 50 characters each |
| `task timeout` | 1–3600 seconds (default 300) |
| `retry count` | 0–5 (default 3) |

---

## WebSocket API

Real-time streaming for live monitoring of agents, tasks, and system events.

### Connection

```
ws://localhost:8000/ws
```

### Configuration

| Setting | Value |
|---------|-------|
| Connection timeout | 300 seconds |
| Max connections per user | 5 |
| Max global connections | 1000 |
| Ping interval | 30 seconds |
| Pong timeout | 10 seconds |

### Message Types

| Type | Direction | Description |
|------|-----------|-------------|
| `CONNECT` / `DISCONNECT` | Both | Connection lifecycle |
| `AUTH` / `AUTH_RESPONSE` | Both | Token-based authentication |
| `PING` / `PONG` | Both | Keep-alive heartbeat |
| `AGENT_STATUS_UPDATE` | Server → Client | Real-time agent state changes |
| `TASK_UPDATE` | Server → Client | Task execution progress |
| `SYSTEM_EVENT` | Server → Client | System-level notifications |
| `METRICS_UPDATE` | Server → Client | Live metrics stream |
| `NOTIFICATION` | Server → Client | User notifications |
| `ERROR` | Server → Client | Error messages |

### Channel Subscriptions

Clients subscribe to channels for filtered updates. Channels are permission-scoped and tenant-isolated.

---

## Agent Types

### Overview

| Agent | Autonomy | Coordination | Use Case |
|-------|----------|-------------|----------|
| **SimpleAgent** | Low | None | Basic message subscriber |
| **TaskExecutorAgent** | Low | Directed | Execute assigned tasks |
| **OrchestratorAgent** | Medium | Central | Coordinate multi-step workflows |
| **AutonomousAgent** | High | Self-organizing | Independent task management |
| **SwarmOrchestrator** | Medium | Swarm | Manage swarm of workers |
| **SwarmWorkerAgent** | Medium | Swarm | Execute swarm tasks |
| **FederatedLearningAgent** | Medium | Federated | Distributed ML training |
| **SafetyAwareAgent** | High | Safety-checked | Safety-validated operations |
| **DecentralizedAgent** | High | P2P (Raft/Gossip) | No central coordinator |
| **VertexAIAgent** | High | AI-powered | Google Gemini integration |

### AutonomousAgent

The core agent type. Makes independent decisions about task acceptance using the **AgentAutonomyService**:

1. **Evaluate** — Score each task offering against capabilities, workload, health
2. **Decide** — Accept tasks above the attractiveness threshold (0.6)
3. **Prioritize** — Order accepted tasks by priority
4. **Execute** — Process tasks sequentially with state tracking
5. **Collaborate** — Request help from other agents when needed

**Decision scoring weights:** 40% priority, 30% capability match, 20% workload capacity, 10% deadline pressure.

### Agent Lifecycle

```
    ┌──────────┐
    │ AVAILABLE │◄──────────────────────────┐
    └────┬─────┘                            │
         │ assign_task()                    │
         ▼                                  │
    ┌──────┐    complete_task()             │
    │ BUSY ├────────────────────────────────┘
    └──┬───┘    fail_task()                 │
       │                                    │
       │ pause() (from AVAILABLE)           │
       │        ┌────────┐                  │
       └───────►│ PAUSED │──── resume() ────┘
                └────────┘

    Any state ──── terminate() ──── TERMINATED
    Any state ──── mark_unhealthy() ──── UNHEALTHY
```

---

## Coordination Patterns

### Orchestrator-Worker

A central orchestrator decomposes tasks and distributes subtasks to specialized workers. Results are aggregated back.

```
         ┌──────────────┐
         │ Orchestrator  │
         └──┬───┬───┬───┘
            │   │   │
         ┌──┘   │   └──┐
         ▼      ▼      ▼
      Worker  Worker  Worker
```

### Hierarchical

Commands flow downward, events flow upward. Peers coordinate laterally within levels.

### Blackboard

Agents read from and write to a shared knowledge base. Each agent monitors relevant domains and contributes when it can.

### Market-Based

Agents bid on tasks via auction. Dynamic pricing discovers optimal resource allocation.

### Swarm Intelligence

Emergent coordination with roles (Leader, Worker, Observer, Coordinator, Specialist). Supports task dependencies and collective metrics.

### Federated Learning

Distributed model training across agents. Only model updates are shared — raw data stays local. Supports model versioning, encrypted updates, and configurable aggregation thresholds.

### Decentralized (P2P)

No central coordinator. Agents use **gossip protocols** for information dissemination and **Raft consensus** for distributed decision-making.

---

## Message Abstraction Layer

### Universal Message Format

Every message across all platforms uses the same structure:

```python
UniversalMessage(
    metadata={"id": "uuid", "timestamp": "ISO8601", "type": "TaskAssigned"},
    routing={"targets": ["nats:agent.tasks", "kafka:events"]},
    payload={"task_id": "123", "data": {...}},
    context={"correlation_id": "abc"},
    security={"encrypted": True},
    tenant_id="tenant-123"
)
```

### Supported Platforms

| Platform | Adapter | Connection Parameter |
|----------|---------|---------------------|
| **NATS** | `NATSAdapter` | `servers: list[str]` |
| **Kafka** | `KafkaAdapter` | `bootstrap_servers: str` |
| **Google Cloud Pub/Sub** | `PubSubAdapter` | `project_id: str` |
| **Advanced Pub/Sub** | `AdvancedPubSubAdapter` | `project_id`, `enable_ordering`, `enable_dead_letter_queue` |
| **Apache Pulsar** | `PulsarAdapter` | `service_url: str` |
| **AWS SNS/SQS** | `SNSSQSAdapter` | `region_name: str` |
| **Google Vertex AI** | `VertexAIAdapter` | `project_id`, `location` (default: `us-central1`) |

### Intelligent Routing

The **AdvancedMessageRouter** selects the best agent for each message using multi-factor scoring:

- **Capability match** — Does the agent have the required skills?
- **Load awareness** — How busy is the agent?
- **Performance history** — What's the agent's success rate?
- **Context relevance** — Is this agent suited for this context?

Routing strategies: `round_robin`, `least_connections`, `capability_based`, `load_balanced`, `priority_queue`.

---

## Domain Model

Built on Domain-Driven Design with immutable aggregates, value objects, and event sourcing.

### AgentAggregate (Root Entity)

The core domain entity representing an autonomous agent:

- **Identity**: `AgentId` (validated, 3–256 chars)
- **Capabilities**: List of `AgentCapability` with proficiency levels (1–5)
- **Status**: State machine (AVAILABLE, BUSY, PAUSED, UNHEALTHY, TERMINATED)
- **Health**: `HealthMetrics` (success rate, response time, CPU, memory)
- **Task tracking**: Counters for assigned, completed, failed tasks
- **Resources**: `ResourceRequirement` (CPU, memory, disk, GPU)

### Domain Events (14 events)

Full event-sourced lifecycle:

| Event | Trigger |
|-------|---------|
| `AgentCreatedEvent` | Agent registered in system |
| `AgentActivatedEvent` | Agent ready for operation |
| `AgentCapabilityAddedEvent` | New skill acquired |
| `AgentCapabilityUpgradedEvent` | Skill proficiency increased |
| `AgentTaskAssignedEvent` | Task received and accepted |
| `AgentTaskCompletedEvent` | Task finished successfully |
| `AgentTaskFailedEvent` | Task execution failed |
| `AgentStatusChangedEvent` | State transition occurred |
| `AgentHealthCheckPassedEvent` | Health check succeeded |
| `AgentHealthCheckFailedEvent` | Health check failed |
| `AgentPausedEvent` | Agent paused |
| `AgentResumedEvent` | Agent resumed |
| `AgentTerminatedEvent` | Agent permanently retired |

### CQRS

Commands and queries are separated with dedicated handlers and dispatched through the `CqrsBus`. Events are published via the `EventBus` and persisted in the `EventStore`.

---

## Security

### Authentication

- **JWT tokens** with tenant claims via `python-jose`
- Configurable algorithm (`HS256`, `HS384`, `HS512`, `RS256`)
- Configurable expiration (default: 24 hours)
- Bearer token authentication on all protected endpoints

### Encryption

- **Fernet symmetric encryption** (AES-128-CBC) via `cryptography`
- Encrypts message payloads at rest in PostgreSQL
- Environment-based key management
- Tamper detection via HMAC

### Tenant Isolation

Every message, agent, query, and API call is scoped to a tenant. Cross-tenant access is prevented at every layer.

### Security Middleware

| Protection | Implementation |
|-----------|----------------|
| CORS | Configurable allowed origins, methods, headers per environment |
| CSP | Content-Security-Policy headers (strict in production) |
| HSTS | Strict-Transport-Security with preload |
| XSS | X-XSS-Protection, X-Content-Type-Options |
| Clickjacking | X-Frame-Options: DENY |
| Cache | no-store, no-cache, private |
| Rate limiting | Per API key, user ID, or IP address |
| Input sanitization | HTML tag stripping, SQL quote escaping, path traversal prevention |
| File upload validation | Extension allowlist, MIME type checking |
| Request tracing | X-Request-ID on every response |

### Security Levels

| Level | CORS | Rate Limit | CSP | Request Logging |
|-------|------|-----------|-----|-----------------|
| `development` | localhost:3000, :8000 | Off | Off | Debug |
| `testing` | localhost:3000, :8000 | On | On | Debug |
| `staging` | staging.agentmesh.ai | On | On | Info |
| `production` | api.agentmesh.ai | On | On | Info |

### Audit Logging

Structured audit logs for all security-relevant operations with data classification, user attribution, and searchable history.

---

## Resilience Patterns

### Circuit Breaker

Prevents cascading failures by tracking consecutive errors and short-circuiting requests to failing services.

| Setting | Default |
|---------|---------|
| Failure threshold | 5 consecutive failures |
| Recovery timeout | 60 seconds |
| Success threshold (half-open) | 2 successes to close |

**States:** CLOSED (normal) → OPEN (failing, reject all) → HALF_OPEN (testing recovery)

```python
breaker = CircuitBreaker(CircuitBreakerConfig(failure_threshold=5))
result = await breaker.execute(my_async_function, arg1, arg2)
```

### Bulkhead Isolation

Isolates resource pools to prevent one failing component from exhausting shared resources.

| Setting | Default |
|---------|---------|
| Max concurrent tasks | 10 |
| Max queue size | 50 |
| Task timeout | 30 seconds |
| Queue timeout | 5 seconds |

```python
bulkhead = Bulkhead(BulkheadConfig(max_concurrent=10, max_queue=50))
result = await bulkhead.execute(my_task)
```

### Retry Policy

Configurable retry with exponential backoff and jitter.

| Setting | Default |
|---------|---------|
| Max attempts | 3 |
| Base delay | 100ms |
| Max delay | 30 seconds |
| Backoff multiplier | 2.0x |
| Jitter | Enabled (100ms range) |

```python
policy = RetryPolicy(RetryConfig(max_attempts=3, base_delay_ms=100))
result = await policy.execute(flaky_operation)
```

---

## Observability

### Prometheus Metrics (25+)

**Message routing:**
- `agentmesh_messages_routed_total` — Counter by tenant, type, strategy
- `agentmesh_message_routing_latency_seconds` — Histogram
- `agentmesh_routing_errors_total` — Counter by error type
- `agentmesh_messages_in_queue` — Gauge per queue

**Agent health:**
- `agentmesh_active_agents` — Gauge by status
- `agentmesh_agent_state_changes_total` — Transition counter
- `agentmesh_health_check_failures_total` — Counter by reason
- `agentmesh_agent_load_percent` — Gauge (0–100)

**Task execution:**
- `agentmesh_task_execution_seconds` — Histogram by task type
- `agentmesh_tasks_completed_total` — Counter by status
- `agentmesh_tasks_in_progress` — Gauge

**Business KPIs:**
- `agentmesh_agents_created_total` — Cumulative count
- `agentmesh_tenant_agents_total` — Per-tenant count
- `agentmesh_collaboration_events_total` — Multi-agent events

### Anomaly Detection

Statistical anomaly detection using z-score analysis on metric streams.

| Setting | Default |
|---------|---------|
| Window size | 30 data points |
| Std deviation threshold | 3.0 |

### Structured Logging

All components use **Loguru** with structured, color-coded, level-aware logging.

---

## Web UI

Flask-based monitoring dashboard available at `http://localhost:5000`:

| Page | Path | Description |
|------|------|-------------|
| Home | `/` | Navigation and overview |
| Tenants | `/tenants` | View and create tenants |
| System Status | `/status` | Overall system health |
| Messages | `/messages` | Browse processed messages |

---

## Testing

```bash
# Run all tests (excluding CLI tests that need google-cloud-aiplatform)
poetry run pytest tests/ --ignore=tests/cli

# Run specific test categories
poetry run pytest tests/unit/           # Unit tests
poetry run pytest tests/integration/    # Integration tests
poetry run pytest tests/e2e/            # End-to-end tests
poetry run pytest tests/performance/    # Performance benchmarks
poetry run pytest tests/cqrs/           # CQRS tests
poetry run pytest tests/mal/            # Message layer tests

# Run with verbose output
poetry run pytest tests/ --ignore=tests/cli -v
```

**Current status:** 246 tests passing, comprehensive coverage across domain logic, use cases, infrastructure adapters, resilience patterns, security, CQRS, and end-to-end workflows.

---

## Project Structure

```
agentmesh-eda/
├── agentmesh/
│   ├── domain/                    # Core business logic (DDD)
│   │   ├── entities/              #   AgentAggregate (root entity)
│   │   ├── value_objects/         #   AgentId, AgentCapability, HealthMetrics, etc.
│   │   ├── domain_events/        #   14 domain events for event sourcing
│   │   ├── services/             #   AgentAutonomyService, AgentLoadBalancerService
│   │   └── ports/                #   Repository and persistence interfaces
│   │
│   ├── application/               # Use cases and DTOs
│   │   └── use_cases/            #   CreateAgentUseCase
│   │
│   ├── infrastructure/            # Technical implementations
│   │   ├── adapters/             #   InMemoryAgentRepository, PostgresAdapter
│   │   ├── resilience/           #   CircuitBreaker, Bulkhead, RetryPolicy
│   │   ├── observability/        #   Prometheus metrics (25+ metrics)
│   │   └── security/            #   AuditLogger
│   │
│   ├── mal/                       # Message Abstraction Layer
│   │   ├── adapters/             #   NATS, Kafka, Pub/Sub, Pulsar, SNS/SQS, Vertex AI
│   │   ├── message.py            #   UniversalMessage format
│   │   ├── router.py             #   Basic message routing
│   │   └── advanced_router.py    #   Intelligent multi-factor routing
│   │
│   ├── aol/                       # Agent Orchestration Layer
│   │   ├── autonomous_agent.py   #   Self-organizing agent
│   │   ├── coordinator.py        #   Agent coordination
│   │   ├── registry.py           #   Agent discovery
│   │   ├── swarm_orchestrator.py #   Swarm coordination
│   │   ├── federated_learning.py #   Distributed ML training
│   │   ├── safety_aware_agent.py #   Safety-validated agent
│   │   └── decentralized_agent.py#   P2P with gossip/Raft
│   │
│   ├── patterns/                  # Multi-agent coordination patterns
│   │   ├── orchestrator_worker.py
│   │   ├── hierarchical.py
│   │   ├── blackboard.py
│   │   └── market_based.py
│   │
│   ├── cqrs/                      # Command Query Responsibility Segregation
│   │   ├── bus.py                #   CqrsBus + EventBus
│   │   ├── command.py, query.py  #   Command and query definitions
│   │   ├── handler.py            #   Command/query handlers
│   │   └── event_store.py        #   Event persistence
│   │
│   ├── epe/                       # Event Processing Engine
│   │   ├── stream_processor.py   #   Event stream processing
│   │   └── anomaly_detection.py  #   Statistical anomaly detection
│   │
│   ├── security/                  # Authentication & encryption
│   │   ├── auth.py               #   JWT token creation/verification
│   │   ├── encryption.py         #   Fernet encryption service
│   │   ├── config.py             #   Environment-based security config
│   │   └── roles.py              #   RBAC role definitions
│   │
│   ├── middleware/                 # HTTP middleware
│   │   ├── security.py           #   Security headers, CORS, CSP, input sanitization
│   │   └── rate_limiting.py      #   Request rate limiting
│   │
│   ├── api/                       # REST API
│   │   ├── fastapi_app.py        #   FastAPI application and routes
│   │   └── validation_models.py  #   Pydantic request/response models
│   │
│   ├── websocket/                 # Real-time WebSocket
│   │   └── websocket_manager.py  #   Connection management, channels, streaming
│   │
│   ├── cli/                       # Command-line interface
│   │   └── main.py               #   CLI commands (tenant, agent, status)
│   │
│   ├── ui/                        # Web UI (Flask)
│   ├── db/                        # Database models (SQLAlchemy)
│   └── utils/                     # Shared utilities and metrics
│
├── tests/
│   ├── unit/                      # Domain and service unit tests
│   ├── integration/               # Infrastructure integration tests
│   ├── e2e/                       # End-to-end workflow tests
│   ├── performance/               # Performance benchmarks
│   ├── cqrs/                      # CQRS-specific tests
│   ├── mal/                       # Message layer tests
│   └── mocks/                     # Shared mock implementations
│
├── docker-compose.yml             # Service orchestration
├── Dockerfile                     # Container image (python:3.10-slim)
├── pyproject.toml                 # Dependencies and project config
└── .env.example                   # Environment variable template
```

---

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Language** | Python | ^3.9 |
| **API Framework** | FastAPI | ^0.109.2 |
| **ASGI Server** | Uvicorn | ^0.27.1 |
| **Database** | PostgreSQL + SQLAlchemy | 13 / ^2.0.25 |
| **Validation** | Pydantic | ^2.5.0 |
| **Auth** | python-jose (JWT) | ^3.3.0 |
| **Encryption** | cryptography (Fernet) | ^42.0.5 |
| **Logging** | Loguru | ^0.7.2 |
| **Metrics** | prometheus-client | ^0.20.0 |
| **Messaging: NATS** | nats-py | ^2.3.1 |
| **Messaging: Kafka** | confluent-kafka | ^2.3.0 |
| **Messaging: Pub/Sub** | google-cloud-pubsub | ^2.19.0 |
| **Messaging: Pulsar** | pulsar-client | ^3.4.0 |
| **Messaging: AWS** | boto3 | ^1.34.5 |
| **AI: Vertex AI** | google-cloud-aiplatform | ^1.37.1 |
| **Monitoring: GCP** | google-cloud-monitoring | ^2.14.0 |
| **Caching** | redis | ^4.5.0 |
| **Testing** | pytest + pytest-asyncio | ^7.4.4 / ^0.23.5 |
| **Linting** | ruff | ^0.12.8 |
| **Docs** | Sphinx | ^7.2.6 |
| **Container** | Docker (python:3.10-slim) | — |
| **Orchestration** | Docker Compose | — |

---

## License

MIT
