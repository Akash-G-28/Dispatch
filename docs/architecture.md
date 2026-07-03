# Architecture

## System Overview

The AI Delivery Control Plane is a human-in-the-loop orchestration layer that converts ambiguous business AI requests into governed, auditable delivery workflows. The architecture enforces explicit approval gates before any external write operations while maintaining full traceability.

## Core Components

### 1. API Layer (`app/api/`)
- **FastAPI Application**: RESTful API with OpenAPI documentation
- **Routes**: 
  - `POST /runs` - Request intake and classification
  - `GET /runs/{run_id}` - State inspection
  - `POST /runs/{run_id}/approve` - Human approval gate
  - `POST /runs/{run_id}/execute` - Idempotent execution
- **Schemas**: Pydantic models for request/response validation

### 2. State Management (`app/state/`)
- **Models**: `WorkflowRun`, `ApprovalRecord`, `RunStatus` enum
- **Repository**: SQLite-backed persistence with audit logging
- **Transitions**: Guarded state machine with allowed transitions
- **Idempotency**: Key-based deduplication to prevent duplicate operations

### 3. Orchestration Engine (`app/orchestration/`)
- **Planner**: Rule-based request classification and standards retrieval
- **Drafter**: Solution brief generation using Jinja2 templates
- **Executor**: Idempotent connector execution with policy enforcement
- **Engine**: Workflow coordination and state transitions

### 4. Connectors (`app/connectors/`)
- **Base**: Abstract connector interface with Sentry tracing
- **GitHub MCP**: Repository and issue management (demo mode)
- **Notion MCP**: Page creation and search (demo mode)
- **Slack MCP**: Notification delivery (demo mode)
- **Demo Mode**: Deterministic, no external side effects

### 5. Core Services (`app/core/`)
- **Config**: Environment-based settings (Pydantic Settings)
- **Policies**: Tool permission matrix (READ, APPROVAL_REQUIRED, DISABLED)
- **Sentry**: Error tracking and performance monitoring

## Workflow State Machine

```
RECEIVED
    ↓
CLASSIFIED
    ↓
DRAFTED
    ↓
PENDING_APPROVAL ←──┐
    ↓                │
APPROVED             │
    ↓                │
EXECUTING            │
    ↓                │
COMPLETED            │
    └────────────────┘
```

**Terminal States**: COMPLETED, FAILED, CANCELLED

**Guarded Transitions**: Each transition is validated against `ALLOWED_TRANSITIONS` matrix in `app/state/transitions.py`

## Data Flow

### Request Intake
1. Business owner submits raw request via `POST /runs`
2. System generates one-time approval token (hashed, stored)
3. Idempotency key checked for duplicate requests
4. Initial state: RECEIVED

### Classification Phase
1. Rule-based classifier analyzes request content
2. Sensitivity level determined (LOW, MEDIUM, HIGH)
3. Value/complexity/risk scorecard generated
4. Standards retrieved from connector (read-only)
5. State transition: RECEIVED → CLASSIFIED

### Solution Brief Drafting
1. Jinja2 templates populated with classification data
2. Solution brief generated (architecture, approach, risks)
3. Pending write actions enumerated
4. State transition: CLASSIFIED → DRAFTED → PENDING_APPROVAL

### Human Approval Gate
1. Approver uses one-time token via `POST /runs/{run_id}/approve`
2. Token hash verified against stored hash
3. Approval record persisted (approver, timestamp, reason)
4. State transition: PENDING_APPROVAL → APPROVED

### Execution Phase
1. Executor verifies approval record and token
2. Policy engine checks tool permissions
3. Connectors execute idempotent operations
4. Artifacts persisted (repo URLs, issue IDs, etc.)
5. State transition: APPROVED → EXECUTING → COMPLETED

## Persistence Layer

### SQLite Schema
- **workflow_runs**: Main workflow state table
- **audit_log**: State transition and operation log
- **effect_ledger**: Idempotency tracking for side effects

### Audit Trail
Every state transition and external operation is logged with:
- Timestamp (UTC)
- Actor (system or human)
- Operation type
- Context/metadata

## Security Boundaries

### Tool Permission Matrix
| Tool | Permission | Rationale |
|------|------------|-----------|
| `github.read_repo` | READ | Safe, read-only |
| `github.create_repo` | APPROVAL_REQUIRED | Write operation |
| `github.create_issue` | APPROVAL_REQUIRED | Write operation |
| `notion.search` | READ | Safe, read-only |
| `notion.create_page` | APPROVAL_REQUIRED | Write operation |
| `slack.send_message` | ALLOWED_AFTER_STATE_CHANGE | Notification only |
| `playwright.browser_run_code_unsafe` | DISABLED | Destructive tool |

### Approval Token Security
- Cryptographically secure random tokens (32 bytes URL-safe)
- SHA-256 hashed before storage
- Single-use (verified against hash)
- Never returned after creation

## Scalability Considerations

### Current Limitations (Demo Mode)
- Single SQLite database (no horizontal scaling)
- In-memory connectors (no external dependencies)
- No distributed locking

### Production Migration Path
1. **Database**: SQLite → PostgreSQL with row-level locking
2. **Connectors**: Demo → MCP with authenticated transports
3. **Queue**: Add task queue (Celery/RQ) for async execution
4. **Caching**: Redis for token validation and rate limiting
5. **Observability**: Enhanced metrics (Prometheus) and tracing (OpenTelemetry)

## Error Handling

### State Machine Guarantees
- Invalid transitions raise `ValueError`
- Failed operations transition to FAILED state
- Cancellation supported from most states
- No silent state corruption

### Connector Error Propagation
- Sentry captures connector exceptions
- Errors persisted in workflow run
- Failed state with error context
- Retry via re-execution (idempotent)

## Monitoring

### Health Check (`GET /health`)
- Service version
- Environment (local/staging/production)
- Connector mode (demo/production)
- Status (ok/degraded)

### Sentry Integration
- Error tracking
- Performance monitoring
- Connector span tracing
- Sensitive data excluded from attributes

## Extension Points

### Adding New Connectors
1. Inherit from `BaseConnector` in `app/connectors/base.py`
2. Implement required methods with Sentry spans
3. Add tool permissions to `TOOL_POLICY`
4. Register in `app/connectors/__init__.py`

### Custom Classifiers
1. Implement classifier interface
2. Replace `RuleBasedClassifier` in orchestration engine
3. Update evaluation rubric in `app/eval/rubric.py`

### Additional Templates
1. Add Jinja2 template to `app/templates/`
2. Reference in drafter with template context
3. Update solution brief schema if needed
