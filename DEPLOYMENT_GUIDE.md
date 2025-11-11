# AgentMesh Deployment Guide

**Version**: 1.0
**Status**: Ready for Production
**Last Updated**: October 29, 2024

---

## Overview

This guide walks through deploying AgentMesh as an autonomous, agentic AI system following enterprise-grade architectural patterns.

### What You'll Deploy

- ✅ Secure agent orchestration system
- ✅ Autonomous agents with intelligent decision-making
- ✅ Multi-tenant message routing
- ✅ Event-driven integration architecture
- ✅ PostgreSQL persistence with encryption
- ✅ Message broker (NATS, Kafka, etc.)

---

## Prerequisites

### System Requirements
- **OS**: Linux, macOS, or Windows (WSL2)
- **CPU**: 4+ cores
- **Memory**: 8GB+ RAM
- **Disk**: 20GB+ available space

### Software Requirements
- Python 3.9+
- Docker & Docker Compose
- PostgreSQL 13+ (or use Docker)
- Message broker (NATS, Kafka - or use Docker)
- Git

### Knowledge Requirements
- Basic understanding of Docker
- Familiarity with environment variables
- PostgreSQL basics helpful but not required

---

## Quick Start (Development)

### Step 1: Clone and Setup

```bash
# Clone repository
git clone https://github.com/your-org/agentmesh.git
cd agentmesh/agentmesh-eda

# Install dependencies
poetry install

# Copy environment template
cp .env.example .env
```

### Step 2: Generate Security Keys

```bash
# Generate encryption key
ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Generate JWT secret
JWT_SECRET=$(openssl rand -hex 32)

# Update .env with generated keys
python << 'EOF'
with open('.env', 'r') as f:
    content = f.read()

content = content.replace('ENCRYPTION_KEY=<generate-a-fernet-key>', f'ENCRYPTION_KEY={ENCRYPTION_KEY}')
content = content.replace('JWT_SECRET_KEY=<generate-a-secret-key>', f'JWT_SECRET_KEY={JWT_SECRET}')

with open('.env', 'w') as f:
    f.write(content)

print(f"✅ Keys configured in .env")
print(f"   ENCRYPTION_KEY={ENCRYPTION_KEY}")
print(f"   JWT_SECRET_KEY={JWT_SECRET}")
EOF
```

### Step 3: Start Services

```bash
# Start Docker containers (PostgreSQL, NATS, etc.)
docker-compose up -d

# Verify services running
docker-compose ps

# Check logs
docker-compose logs -f agentmesh
```

### Step 4: Verify Installation

```bash
# Run tests
pytest tests/ -v

# Run specific test suites
pytest tests/unit/domain/ -v  # Unit tests
pytest tests/integration/ -v   # Integration tests
pytest tests/e2e/ -v          # End-to-end tests

# Check coverage
pytest tests/ --cov=agentmesh
```

### Step 5: Start Application

```bash
# Development server with auto-reload
poetry run uvicorn agentmesh.icl.api_gateway:app --reload

# Application available at: http://localhost:8000

# API documentation: http://localhost:8000/docs
```

---

## Production Deployment

### Architecture Overview

```
Load Balancer (nginx/ALB)
    ↓
API Gateway (FastAPI) × N (horizontal scaling)
    ↓
Agent Orchestration × N (stateless)
    ↓
┌─────────────────────────────────────┐
│ PostgreSQL                          │
│ (Encrypted Payloads + Event Store) │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ Message Broker                      │
│ (NATS / Kafka cluster)             │
└─────────────────────────────────────┘
```

### Step 1: Configure Production Environment

Create `production.env`:
```bash
# Security
ENCRYPTION_KEY=<from-secrets-manager>
JWT_SECRET_KEY=<from-secrets-manager>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=8

# Database
DATABASE_URL=postgresql://user:pass@db-prod.internal:5432/agentmesh

# Message Broker
NATS_URL=nats://nats-prod.internal:4222
# OR
KAFKA_BROKERS=kafka-1.internal:9092,kafka-2.internal:9092,kafka-3.internal:9092

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Observability
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

# Limits
MAX_AGENTS_PER_TENANT=10000
MAX_TASKS_PER_HOUR_PER_TENANT=100000
```

### Step 2: Deploy to Kubernetes

#### Create Deployment Manifest

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agentmesh-api
  labels:
    app: agentmesh
spec:
  replicas: 3  # Horizontal scaling
  selector:
    matchLabels:
      app: agentmesh
  template:
    metadata:
      labels:
        app: agentmesh
    spec:
      containers:
      - name: agentmesh
        image: agentmesh:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: production
        - name: ENCRYPTION_KEY
          valueFrom:
            secretKeyRef:
              name: agentmesh-secrets
              key: encryption-key
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: agentmesh-secrets
              key: jwt-secret
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: agentmesh-secrets
              key: database-url
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1024Mi
      imagePullPolicy: Always
---
apiVersion: v1
kind: Service
metadata:
  name: agentmesh-service
spec:
  type: LoadBalancer
  selector:
    app: agentmesh
  ports:
  - port: 80
    targetPort: 8000
```

#### Deploy

```bash
# Create secrets
kubectl create secret generic agentmesh-secrets \
  --from-literal=encryption-key=$ENCRYPTION_KEY \
  --from-literal=jwt-secret=$JWT_SECRET \
  --from-literal=database-url=$DATABASE_URL

# Deploy
kubectl apply -f deployment.yaml

# Verify
kubectl get pods -l app=agentmesh
kubectl logs deployment/agentmesh-api

# Scale if needed
kubectl scale deployment agentmesh-api --replicas=5
```

### Step 3: Database Migration

```bash
# Create database schema
python << 'EOF'
from agentmesh.db.database import Base, engine

# Create all tables
Base.metadata.create_all(bind=engine)
print("✅ Database schema created")
EOF

# Run migrations (if using Alembic)
alembic upgrade head
```

### Step 4: Message Broker Setup

#### NATS

```bash
# Start NATS cluster
docker run -d \
  -p 4222:4222 \
  -p 8222:8222 \
  nats:latest

# Verify
nats server list
```

#### Kafka

```bash
# Start Kafka cluster (Docker Compose)
docker-compose up -d kafka zookeeper

# Create topics
kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --topic agent-events \
  --partitions 3 \
  --replication-factor 3
```

### Step 5: Monitoring & Observability

#### Prometheus Setup

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'agentmesh'
    static_configs:
      - targets: ['localhost:9090']
```

#### Grafana Dashboard

```bash
# Start Grafana
docker run -d \
  -p 3000:3000 \
  grafana/grafana:latest

# Add Prometheus datasource
# URL: http://prometheus:9090

# Import AgentMesh dashboard
# Located at: grafana/dashboards/agentmesh.json
```

#### Key Metrics to Monitor

```
- messages_sent_total (by platform, topic)
- agent_tasks_completed_total (by agent_id)
- agent_tasks_failed_total (by agent_id)
- event_store_events_saved_total
- commands_dispatched_total
- http_requests_total
- http_request_duration_seconds
```

### Step 6: Health Checks

```bash
# Liveness check
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/ready

# Status endpoint
curl http://localhost:8000/status
```

---

## Scaling Considerations

### Horizontal Scaling

**API Gateway** (stateless):
```
Load Balancer
  ├─ API Gateway 1
  ├─ API Gateway 2
  └─ API Gateway 3
```

**Agents** (distributed):
```
Agent Pool (region 1): 100 agents
Agent Pool (region 2): 100 agents
Agent Pool (region 3): 100 agents
```

### Vertical Scaling

**CPU**: 4 → 8 cores
**Memory**: 8GB → 16GB
**Database**: Add read replicas

### Database Optimization

```sql
-- Create indexes
CREATE INDEX idx_agent_tenant_status
  ON agent(tenant_id, status);

CREATE INDEX idx_message_tenant_type
  ON message(tenant_id, message_type);

-- Partitioning (large deployments)
CREATE TABLE message_2024_Q4
  PARTITION OF message
  FOR VALUES FROM ('2024-10-01') TO ('2025-01-01');
```

---

## Security Checklist

- [ ] ENCRYPTION_KEY from secure vault (not in code)
- [ ] JWT_SECRET_KEY from secure vault
- [ ] DATABASE_URL with strong password
- [ ] HTTPS enabled on API Gateway
- [ ] Rate limiting configured per tenant
- [ ] WAF (Web Application Firewall) enabled
- [ ] VPC security groups configured
- [ ] Audit logging enabled
- [ ] Regular backups configured
- [ ] Disaster recovery plan tested

---

## Backup & Recovery

### Daily Backups

```bash
# PostgreSQL backup
pg_dump agentmesh > backup-$(date +%Y%m%d).sql

# Or use managed backups (AWS RDS, CloudSQL)
```

### Recovery Process

```bash
# Stop application
kubectl scale deployment agentmesh-api --replicas=0

# Restore database
psql agentmesh < backup-20241029.sql

# Restart application
kubectl scale deployment agentmesh-api --replicas=3

# Verify
curl http://localhost:8000/health
```

---

## Troubleshooting

### Common Issues

**Problem**: Agent not accepting tasks
```
Solution: Check agent health status
curl http://localhost:8000/agents/{agent_id}/health

Check agent workload
curl http://localhost:8000/agents/{agent_id}/status
```

**Problem**: High latency in task assignment
```
Solution: Check message broker
docker-compose logs nats

Check database performance
EXPLAIN ANALYZE SELECT ... FROM agent;

Consider adding database indexes
```

**Problem**: Out of memory
```
Solution: Reduce task queue size per agent
Update autonomy_service.max_concurrent_tasks = 3

Increase container memory limits
```

---

## Maintenance

### Regular Tasks

**Daily**:
- Monitor error rates
- Check system health
- Review agent utilization

**Weekly**:
- Backup database
- Review logs for patterns
- Update security patches

**Monthly**:
- Performance analysis
- Capacity planning
- Security audit

### Updates

```bash
# Update AgentMesh
docker pull agentmesh:1.1.0
kubectl set image deployment/agentmesh-api \
  agentmesh=agentmesh:1.1.0

# Verify rolling update
kubectl rollout status deployment/agentmesh-api

# Rollback if needed
kubectl rollout undo deployment/agentmesh-api
```

---

## Support

### Logs Location

```
Docker Compose: docker-compose logs agentmesh
Kubernetes: kubectl logs deployment/agentmesh-api
File-based: /var/log/agentmesh/application.log
```

### Getting Help

1. Check `IMPLEMENTATION_GUIDE.md` for common questions
2. Review `claude.md` for architectural principles
3. Check logs for error details
4. See `docs/ADR-*.md` for design decisions

---

## Appendix: Environment Variables

All variables documented in `.env.example`. Key ones:

| Variable | Required | Example |
|----------|----------|---------|
| ENCRYPTION_KEY | ✅ | 2FZWFO3VEVZVU0VYOD... |
| JWT_SECRET_KEY | ✅ | a1b2c3d4e5f6g7h8i9j0... |
| DATABASE_URL | ✅ | postgresql://user:pass@host:5432/db |
| NATS_URL | ⏳ | nats://localhost:4222 |
| ENVIRONMENT | ✅ | production |
| LOG_LEVEL | ✅ | INFO |

---

**Status**: ✅ Ready for Production
**Last Reviewed**: October 29, 2024
**Next Review**: 30 days
