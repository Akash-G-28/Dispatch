# Design Decisions

This document captures the key architectural and technical decisions made during the development of the AI Delivery Control Plane, along with their rationale and trade-offs.

## 1. SQLite for Persistence (Demo Mode)

**Decision**: Use SQLite as the primary database for the reference implementation.

**Rationale**:
- Zero configuration required - no external database setup
- Single-file storage simplifies deployment and testing
- Sufficient for demo and single-worker scenarios
- Easy migration path to PostgreSQL for production

**Trade-offs**:
- Limited concurrency support (write locks)
- No horizontal scaling capability
- Not suitable for high-throughput production workloads

**Migration Path**: Replace `SQLiteRunRepository` with `PostgreSQLRunRepository` using SQLAlchemy async patterns.

## 2. Rule-Based Classification (vs LLM)

**Decision**: Implement a rule-based classifier using keyword matching and heuristics.

**Rationale**:
- Deterministic behavior for predictable evaluation
- No external API dependencies or costs
- Fast execution (sub-100ms)
- Transparent logic for security review
- Easy to test and validate

**Trade-offs**:
- Limited nuance compared to LLM-based classification
- Requires manual rule updates for new patterns
- May misclassify edge cases

**Migration Path**: Replace `RuleBasedClassifier` with LLM-based classifier using structured output prompts (already included in `app/prompts/`).

## 3. One-Time Approval Tokens

**Decision**: Use cryptographically secure one-time tokens for approval verification.

**Rationale**:
- Prevents token reuse attacks
- No need for persistent session management
- Simple implementation with `secrets.token_urlsafe()`
- Hashed storage prevents token leakage even from database dumps

**Trade-offs**:
- Token must be returned only on initial creation
- Lost tokens require workflow restart
- No built-in expiration (could add timestamp validation)

**Future Enhancement**: Add token expiration (e.g., 24-hour TTL) and rotation mechanisms.

## 4. Idempotency Keys

**Decision**: Require client-provided idempotency keys for all requests.

**Rationale**:
- Prevents duplicate workflow runs on retry
- Enables safe client-side retry logic
- Simple deduplication without distributed locks
- Aligns with payment API patterns (Stripe, etc.)

**Trade-offs**:
- Requires client to manage key generation
- Key collisions possible with poor key generation strategy
- Additional database query on every request

**Best Practice**: Use UUIDs or composite keys (user_id + timestamp + request_hash).

## 5. State Machine with Guarded Transitions

**Decision**: Implement explicit state machine with allowed transition matrix.

**Rationale**:
- Prevents invalid state transitions
- Self-documenting workflow logic
- Easy to visualize and debug
- Enables state-based policy enforcement

**Trade-offs**:
- Additional complexity for simple workflows
- Requires explicit transition logic for every state change
- May feel rigid for flexible use cases

**Alternative**: Event sourcing with event replay (considered but rejected for demo simplicity).

## 6. Tool Permission Matrix

**Decision**: Centralize tool permissions in a declarative policy matrix.

**Rationale**:
- Single source of truth for security policy
- Easy to audit and review
- Enables runtime permission checks
- Clear separation of policy from implementation

**Trade-offs**:
- Requires policy updates for new tools
- No role-based access control (RBAC) in current implementation
- Static permissions (no context-aware policies)

**Future Enhancement**: Add RBAC with roles (requester, approver, admin) and context-aware policies.

## 7. Demo Mode Connectors

**Decision**: Implement deterministic demo connectors that don't call external APIs.

**Rationale**:
- Safe for development and testing
- No credential management required
- Predictable behavior for evaluation
- Demonstrates integration boundaries without dependencies

**Trade-offs**:
- No real external side effects
- Limited value for production use cases
- May mask integration issues

**Migration Path**: Replace demo implementations with MCP client calls using authenticated transports.

## 8. Jinja2 Templates for Artifact Generation

**Decision**: Use Jinja2 templates for solution briefs and other artifacts.

**Rationale**:
- Familiar template syntax
- Good performance for simple templates
- Easy to maintain and update
- Supports template inheritance

**Trade-offs**:
- Limited logic compared to code generation
- Template complexity can grow unbounded
- No built-in validation of generated content

**Alternative**: LLM-based generation with structured output (considered but rejected for deterministic demo).

## 9. Sentry for Error Tracking

**Decision**: Integrate Sentry SDK for error tracking and performance monitoring.

**Rationale**:
- Production-ready error tracking
- Automatic exception capture
- Performance monitoring with spans
- Industry-standard tooling

**Trade-offs**:
- External dependency on Sentry service
- Requires DSN configuration
- Potential cost at scale

**Alternative**: Self-hosted error tracking (Sentry self-hosted or alternative solutions).

## 10. FastAPI Framework

**Decision**: Use FastAPI as the web framework.

**Rationale**:
- Native async support
- Automatic OpenAPI documentation
- Type-safe with Pydantic integration
- High performance
- Modern Python ecosystem

**Trade-offs**:
- Smaller ecosystem compared to Django
- Less built-in functionality (auth, admin, etc.)
- Requires manual implementation of some features

**Alternative Considered**: Django (rejected for async complexity), Flask (rejected for less type safety).

## 11. Pydantic for Data Validation

**Decision**: Use Pydantic models throughout for request/response validation.

**Rationale**:
- Type safety and automatic validation
- Clear schema definitions
- Good IDE support
- Serialization with `.model_dump()`
- Compatible with FastAPI

**Trade-offs**:
- Additional dependency
- Learning curve for complex validators
- Performance overhead for large payloads

**Alternative**: Manual validation with dataclasses (rejected for less safety).

## 12. Separate Audit Log

**Decision**: Maintain separate audit log table from main workflow state.

**Rationale**:
- Immutable audit trail
- Queryable history independent of current state
- Supports compliance requirements
- Enables replay and debugging

**Trade-offs**:
- Additional storage requirements
- Need to manage log retention
- Potential consistency issues (mitigated with transactions)

**Future Enhancement**: Add log rotation, archiving, and export capabilities.

## 13. No Built-in Authentication

**Decision**: Omit authentication/authorization from the reference implementation.

**Rationale**:
- Focus on core workflow orchestration
- Authentication patterns vary by organization
- Can be added via middleware (OAuth, JWT, etc.)
- Reduces complexity for demo

**Trade-offs**:
- Not production-ready as-is
- Requires security layer before deployment
- No user management

**Recommended Integration**: Add FastAPI middleware for OAuth2/JWT authentication.

## 14. Effect Ledger for Idempotency

**Decision**: Track external side effects in a separate ledger table.

**Rationale**:
- Prevents duplicate external operations
- Enables safe retry logic
- Clear record of what was executed
- Supports rollback scenarios

**Trade-offs**:
- Additional database operations
- Ledger growth over time
- Requires cleanup strategy

**Future Enhancement**: Add ledger compaction and archival.

## 15. Explicit Approval Gate

**Decision**: Require explicit human approval before any write operations.

**Rationale**:
- Human-in-the-loop governance
- Prevents autonomous AI actions
- Clear accountability
- Aligns with enterprise AI governance requirements

**Trade-offs**:
- Slower workflow execution
- Requires human availability
- May not scale for high-volume operations

**Alternative**: Automated approval for low-risk workflows (future enhancement with risk-based policies).

## 16. No Distributed Locking

**Decision**: Use database-level locking instead of distributed locks.

**Rationale**:
- Simpler implementation for demo
- SQLite provides adequate locking for single-worker scenarios
- Avoids Redis/etcd dependencies

**Trade-offs**:
- No support for multiple workers
- Potential contention under load
- Not production-ready for horizontal scaling

**Migration Path**: Add Redis-based distributed locks for multi-worker deployments.

## 17. Health Check Endpoint

**Decision**: Include simple health check endpoint with configuration info.

**Rationale**:
- Standard operational practice
- Enables load balancer health checks
- Provides visibility into connector mode
- Simple to implement and monitor

**Trade-offs**:
- Limited diagnostic information
- No deep health checks (database, external services)

**Future Enhancement**: Add dependency health checks (database, connectors, etc.).

## 18. Docker Support

**Decision**: Include Dockerfile and docker-compose.yml.

**Rationale**:
- Standard containerization
- Easy local development setup
- Production deployment path
- Environment consistency

**Trade-offs**:
- Additional complexity for simple demo
- Container management overhead

**Alternative**: Pure Python deployment (rejected for production readiness).

## Summary of Key Principles

1. **Safety First**: All write operations require explicit approval
2. **Idempotency**: Safe retry logic at every layer
3. **Auditability**: Complete traceability of all operations
4. **Simplicity**: Demo mode with clear production migration paths
5. **Type Safety**: Leverage Python type hints and Pydantic throughout
6. **Observability**: Built-in error tracking and logging
7. **Extensibility**: Clear extension points for connectors and classifiers
