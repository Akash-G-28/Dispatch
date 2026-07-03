# Security Model

This document describes the security architecture, threat model, and security controls implemented in the AI Delivery Control Plane.

## Threat Model

### Primary Threats Addressed

1. **Unauthorized External Writes**: Preventing AI systems from creating external resources without human approval
2. **Token Replay Attacks**: Preventing reuse of approval tokens
3. **Privilege Escalation**: Ensuring tools cannot exceed their permitted permissions
4. **Data Exfiltration**: Preventing sensitive data from leaking through logs or monitoring
5. **State Corruption**: Ensuring workflow state cannot be manipulated to bypass approval gates
6. **Idempotency Bypass**: Preventing duplicate operations that could cause unintended side effects

### Assumptions

- Trusted internal network (no TLS required for demo mode)
- Database access is restricted to application layer
- Approval tokens are transmitted over secure channels in production
- Human approvers are authenticated via external system (not implemented in demo)

## Security Controls

### 1. Approval Gate

**Control**: Explicit human approval required before any write operations.

**Implementation**:
- One-time cryptographically secure approval tokens
- Token hash stored in database (token never returned after creation)
- Approval record persisted with approver identity and timestamp
- Executor verifies both approval record and token hash before execution

**Threats Mitigated**:
- Unauthorized external writes
- Autonomous AI actions

**Limitations**:
- No built-in approver authentication (requires external integration)
- Token must be transmitted securely to approver

### 2. Tool Permission Matrix

**Control**: Declarative permissions for each tool with runtime enforcement.

**Implementation**:
```python
TOOL_POLICY = {
    "github.read_repo": ToolPermission.READ,
    "github.create_repo": ToolPermission.APPROVAL_REQUIRED,
    "github.create_issue": ToolPermission.APPROVAL_REQUIRED,
    "notion.search": ToolPermission.READ,
    "notion.create_page": ToolPermission.APPROVAL_REQUIRED,
    "slack.send_message": ToolPermission.ALLOWED_AFTER_STATE_CHANGE,
    "playwright.browser_run_code_unsafe": ToolPermission.DISABLED,
}
```

**Threats Mitigated**:
- Privilege escalation
- Destructive tool usage

**Limitations**:
- Static permissions (no context-aware policies)
- No role-based access control

### 3. State Machine Guards

**Control**: Allowed transitions enforced at runtime.

**Implementation**:
```python
ALLOWED_TRANSITIONS = {
    RunStatus.PENDING_APPROVAL: {RunStatus.APPROVED, RunStatus.CANCELLED},
    RunStatus.APPROVED: {RunStatus.EXECUTING, RunStatus.CANCELLED},
    # ...
}
```

**Threats Mitigated**:
- State corruption
- Bypassing approval gates

**Limitations**:
- Requires database-level enforcement for true security
- Direct database access could bypass guards

### 4. Idempotency Keys

**Control**: Client-provided keys prevent duplicate operations.

**Implementation**:
- Unique constraint on idempotency_key in database
- Existing run returned if key matches
- Prevents duplicate repositories, issues, etc.

**Threats Mitigated**:
- Idempotency bypass
- Unintended side effects from retries

**Limitations**:
- Requires clients to generate unique keys
- Key collisions possible with poor generation strategy

### 5. Token Security

**Control**: Cryptographically secure tokens with hashed storage.

**Implementation**:
- `secrets.token_urlsafe(32)` for token generation
- SHA-256 hashing before database storage
- Token excluded from API responses after creation
- Constant-time comparison for verification

**Threats Mitigated**:
- Token replay attacks
- Token leakage from database dumps

**Limitations**:
- No token expiration in current implementation
- Lost tokens require workflow restart

### 6. Audit Logging

**Control**: Complete audit trail of all state transitions and operations.

**Implementation**:
- Separate audit_log table
- Every transition logged with timestamp, actor, and context
- Connector operations logged with Sentry spans
- Immutable audit trail (no updates to audit records)

**Threats Mitigated**:
- Undetected state manipulation
- Lack of accountability

**Limitations**:
- Audit log storage growth over time
- No built-in log rotation or archival

### 7. Data Sanitization

**Control**: Sensitive data excluded from logs and monitoring.

**Implementation**:
- Approval token excluded from API responses
- Raw request content not sent to Sentry
- PII filtering in connector implementations
- Environment variables for secrets (never committed)

**Threats Mitigated**:
- Data exfiltration through logs
- Credential leakage

**Limitations**:
- Requires manual sanitization in connector implementations
- No automatic PII detection

### 8. Demo Mode Isolation

**Control**: Connectors run in deterministic demo mode by default.

**Implementation**:
- No external API calls in demo mode
- Deterministic responses for testing
- Clear configuration flag (CONNECTOR_MODE=demo)

**Threats Mitigated**:
- Accidental production actions during development
- Credential exposure in demo environment

**Limitations**:
- Not a security control for production deployments
- Requires mode verification before production use

## Security Boundaries

### Application Layer
- FastAPI application with Pydantic validation
- Input sanitization and type checking
- SQL injection prevention via parameterized queries

### State Layer
- SQLite database with file permissions
- Transactional state updates
- Foreign key constraints

### Connector Layer
- Permission checks before tool execution
- Sentry tracing without sensitive data
- MCP transport isolation (future)

### Infrastructure Layer
- Environment variable configuration
- No hardcoded credentials
- Docker container isolation

## Recommended Production Enhancements

### 1. Authentication & Authorization
- Add OAuth2/JWT authentication middleware
- Implement role-based access control (RBAC)
- Approver identity verification
- Multi-factor approval for high-risk operations

### 2. Network Security
- TLS for all API endpoints
- Network segmentation for database access
- API rate limiting
- IP allowlisting for internal services

### 3. Secrets Management
- HashiCorp Vault or AWS Secrets Manager
- Rotated credentials for connectors
- Temporary credentials with time-bound expiry
- No secrets in environment variables

### 4. Database Security
- PostgreSQL with row-level security
- Encrypted database storage
- Regular database backups with encryption
- Database access logging

### 5. Token Enhancements
- Token expiration (e.g., 24-hour TTL)
- Token rotation mechanism
- One-time use enforcement at database level
- Token revocation capability

### 6. Monitoring & Alerting
- Security event logging (SIEM integration)
- Anomaly detection for unusual patterns
- Failed approval attempt alerting
- Connector failure monitoring

### 7. Compliance Features
- Data retention policies
- GDPR/CCPA compliance controls
- Audit log export capabilities
- Compliance reporting

## Security Testing

### Current Test Coverage
- Approval gate enforcement (`tests/test_approval_gate.py`)
- Idempotency guarantees (`tests/test_executor_idempotency.py`)
- End-to-end workflow security (`tests/test_end_to_end.py`)

### Recommended Security Tests
- Penetration testing for approval bypass
- Token replay attack simulation
- SQL injection testing
- Authorization boundary testing
- Rate limiting validation
- Input fuzzing for API endpoints

## Incident Response

### Detection
- Sentry error alerts
- Failed approval attempt monitoring
- Unusual state transition detection
- Connector failure rate monitoring

### Response Procedures
1. **Immediate**: Disable affected connectors
2. **Investigation**: Review audit logs for suspicious activity
3. **Containment**: Revoke active approval tokens
4. **Recovery**: Restore from database backup if needed
5. **Post-Mortem**: Document incident and implement controls

## Compliance Considerations

### SOC 2 Type II
- Access control (authentication, authorization)
- Change management (approval gates)
- Data integrity (audit logging)
- Availability (health checks, monitoring)

### ISO 27001
- Information security policies
- Access control mechanisms
- Cryptographic controls (token hashing)
- Operations security (audit trails)

### GDPR
- Data minimization in logs
- Right to be forgotten (data retention)
- Data breach notification procedures
- Privacy by design (token security)

## Security Checklist

Before production deployment:

- [ ] Enable TLS for all endpoints
- [ ] Implement authentication middleware
- [ ] Configure secrets management
- [ ] Migrate to PostgreSQL with encryption
- [ ] Enable Sentry DSN with error tracking
- [ ] Set up log aggregation and monitoring
- [ ] Configure rate limiting
- [ ] Implement RBAC for approvers
- [ ] Add token expiration
- [ ] Enable database backups
- [ ] Configure network security groups
- [ ] Run security penetration testing
- [ ] Review and approve tool permissions
- [ ] Set up security incident response process
- [ ] Document security architecture for auditors

## Known Limitations

1. **No Authentication**: Demo mode lacks user authentication
2. **Single Database**: SQLite not suitable for production
3. **No Rate Limiting**: Vulnerable to abuse in production
4. **No Input Validation Beyond Pydantic**: Additional sanitization may be needed
5. **No CSRF Protection**: Required for web UI integration
6. **No Resource Limits**: No memory/CPU constraints on operations
7. **No Dependency Scanning**: Automated vulnerability scanning not configured

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Controls](https://www.cisecurity.org/controls/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
