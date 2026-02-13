# AgentMesh EDA - Audit Fixes

## CRITICAL - App Cannot Run

- [x] **FIX-1**: Syntax error in `agentmesh/middleware/security.py:366-368` — double `else` clause in `_add_cors_headers`
- [x] **FIX-2**: Production code imports from test modules in `agentmesh/api/fastapi_app.py:154-157`
- [x] **FIX-3**: Duplicate `create_agent` route definition in `agentmesh/api/fastapi_app.py:225-324`
- [x] **FIX-4**: Zero tests pass — missing exports (`CircuitBreakerState`, `CircuitBreakerConfig`, `Bulkhead`, `RetryConfig`) cause 6 collection errors
- [x] **FIX-5**: Non-unique event IDs using `hash(datetime.utcnow())` in all domain events — should use `uuid.uuid4()`

## HIGH - Security Vulnerabilities

- [x] **FIX-6**: Broken SQL "sanitizer" using regex blocklist — replaced with quote escaping + null byte removal
- [x] **FIX-7**: Incomplete HTML sanitizer missing 100+ event handlers, SVG vectors, entity encoding bypasses — replaced with tag-stripping approach
- [ ] **FIX-8**: API key validation is format-only — no lookup against stored keys
- [ ] **FIX-9**: Hardcoded uptime/metrics in health check and metrics endpoints
- [ ] **FIX-10**: CORS wildcard `*` fallback combined with `allow_credentials=True`
- [x] **FIX-11**: File upload extension check broken — `txt` vs `.txt` mismatch in set comparison
- [ ] **FIX-12**: No authentication enforcement — `HTTPBearer` defined but never used in route dependencies

## MEDIUM - Architectural Issues

- [x] **FIX-13**: No production `AgentRepositoryPort` adapter — created `InMemoryAgentRepository` in infrastructure/adapters
- [ ] **FIX-14**: Global singletons in encryption, safety orchestrator, coordinator break testability
- [ ] **FIX-15**: Stub implementations shipped as production code (Raft voting, gossip, shared knowledge)
- [ ] **FIX-16**: Mixed async/sync — use cases are sync but called with `await` in FastAPI routes
- [x] **FIX-17**: Duplicate Pydantic models — `AgentListResponse`/`ErrorResponse` defined locally and imported
- [x] **FIX-18**: Deprecated `declarative_base()` in `agentmesh/db/database.py`
- [x] **FIX-19**: `ruff` version conflict — declared twice in `pyproject.toml` with `^0.1.11` and `^0.12.8`

## LOW - Code Quality

- [x] **FIX-20**: CSP header set to object instead of string in security middleware
- [ ] **FIX-21**: No correlation ID propagation beyond audit logger
- [ ] **FIX-22**: Unsafe async state mutation without locks in `AutonomousAgent`
- [ ] **FIX-23**: Silent data loss on decryption failure in postgres adapter
- [ ] **FIX-24**: Hardcoded thresholds (timeouts, retries, capacity) throughout codebase

## Additional Fixes (discovered during test repair)

- [x] **FIX-25**: Prometheus counter `EVENT_STORE_EVENTS_SAVED` missing `tenant_id` label — caused all CQRS/event store tests to fail
- [x] **FIX-26**: `AnomalyDetector.detect()` returned False for anomalous values when std_dev=0 (identical training data)
- [x] **FIX-27**: `AuditLogger.log_action()` ignored `data_classification` from details dict
- [x] **FIX-28**: `create_access_token()` requires `tenant_id` parameter but `conftest.py` fixture didn't pass it
- [x] **FIX-29**: Missing `ENCRYPTION_KEY`/`JWT_SECRET_KEY` env vars for test suite — added defaults in conftest.py
- [x] **FIX-30**: `AgentCoordinator` missing `coordinate_task()` method required by tests
- [x] **FIX-31**: Performance test `test_agent_creation_scalability` — IndexError on `throughputs[5]` (only 5 elements)
- [x] **FIX-32**: Performance test `test_message_routing_throughput` — `avg_latency` compared total time vs per-message threshold
- [x] **FIX-33**: Performance test `test_database_connection_pool_performance` — sequential simulation can't demonstrate pool size benefits
- [x] **FIX-34**: Bulkhead circuit breaker integration test used `failure_threshold=2` but only recorded 1 failure before checking state
- [x] **FIX-35**: Duplicate `test_cli_no_command` function in `tests/cli/test_main.py`
- [x] **FIX-36**: Resilience modules completely rewritten: circuit_breaker.py, bulkhead.py, retry_policy.py — added all missing classes, dataclasses, exception types, and backwards-compatible aliases

## Test Results

- **Before**: 0 tests passing, 6 collection errors
- **After**: 230 tests passing, 0 failures, 0 errors
- **CLI tests**: 1 collection error (missing `google-cloud-aiplatform` dependency — infrastructure issue)
