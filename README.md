# AI Delivery Control Plane

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A production-style FastAPI service that converts a vague business AI request into a structured
classification, standards-grounded solution brief, explicitly approved delivery plan, idempotent
GitHub bootstrap, Slack update, and auditable execution trace.

> **Status:** Alpha reference implementation. External connectors run in deterministic demo mode;
> they do not create real GitHub, Notion, or Slack resources until their MCP transports are implemented.

## Why this exists

AI platform teams rarely struggle to generate one answer. The harder problem is converting ambiguous
demand into a controlled delivery process without losing ownership, approval, or traceability. This
project makes that operational layer concrete.

## What it demonstrates

- Durable SQLite workflow state with guarded transitions
- Conservative request classification and a value/complexity/risk scorecard
- Read-only standards retrieval before approval
- One-time approval tokens before every delivery write
- An idempotency ledger that prevents duplicate repositories and issues on retries
- Connector adapters with Sentry spans around external calls
- Demo connectors that run without external accounts and preserve real integration boundaries

The included connector implementations are intentionally safe demo adapters. Replace their method
bodies with MCP client calls after adding credentials; policy checks, tracing, orchestration, and
idempotency remain outside the transport layer.

## Workflow

```
Business Request
      ↓
Classification
      ↓
Solution Brief
      ↓
Human Approval
      ↓
Idempotent Execution
      ↓
Audit Trail
```

**State Machine**: `RECEIVED → CLASSIFIED → DRAFTED → PENDING_APPROVAL → APPROVED → EXECUTING → COMPLETED`

Failures enter `FAILED`; cancellation is supported by the state model. The planner may read standards,
but cannot write. The executor refuses to run without a stored approval record and matching token.

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
python -m uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for the interactive API.

## Demo flow

Create a run. Save the `approval_token`: it is returned only on first creation.

```bash
curl -X POST http://localhost:8000/runs -H "Content-Type: application/json" -d '{
  "requester":"business-owner",
  "title":"Monthly exposure commentary",
  "raw_request":"Can AI help automate monthly exposure commentary generation?",
  "idempotency_key":"exposure-commentary-demo-001"
}'
```

Approve, then execute using the token from the first response:

```bash
curl -X POST http://localhost:8000/runs/RUN_ID/approve -H "Content-Type: application/json" -d '{
  "approved_by":"control-owner", "approval_token":"TOKEN"
}'
curl -X POST http://localhost:8000/runs/RUN_ID/execute -H "Content-Type: application/json" -d '{
  "approval_token":"TOKEN"
}'
```

Repeating `POST /runs` with the same idempotency key returns the existing run. Repeating execute after
completion returns its existing artifacts. No connector write occurs before approval.

## API

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/runs` | Classify, retrieve standards, draft, and pause for approval |
| `GET` | `/runs/{run_id}` | Read current state and artifacts |
| `POST` | `/runs/{run_id}/approve` | Record a named human decision using the run token |
| `POST` | `/runs/{run_id}/execute` | Perform approved, idempotent delivery actions |
| `GET` | `/health` | Check service configuration |

## Test

```bash
pytest
```

Tests cover sensitive-data classification, policy and state approval gates, the durable effect ledger,
and the complete intake-to-delivery flow.

Run the small classification evaluation separately:

```bash
python -m app.eval.run_eval
```

## Production integration path

1. Implement authenticated JSON-RPC/MCP transports in `app/connectors/`.
2. Replace the local classifier with an LLM structured-output adapter using the supplied prompt.
3. Move SQLite to Postgres and add row-level concurrency controls for multiple workers.
4. Store approval token hashes in a secrets-aware store and add token expiry/rotation.
5. Add connector timeouts, rate-limit handling, and retries only where calls are idempotent.
6. Configure `SENTRY_DSN`; keep sensitive request content out of span attributes.

## Success criteria

- 90%+ valid classifications on a curated evaluation set
- Zero duplicate side effects under retries
- 100% of write actions require approval
- Every run produces state-transition audit records and connector traces
- Sample flow completes in under 60 seconds

## Documentation

- [Architecture](docs/architecture.md) - System architecture and component design
- [Design Decisions](docs/design-decisions.md) - Key technical decisions and trade-offs
- [Security Model](docs/security-model.md) - Security architecture and threat model
- [Roadmap](docs/roadmap.md) - Development roadmap and future enhancements

## Security and scope

This repository is a reference implementation, not a hosted service. Never commit connector tokens or
production data. Review [SECURITY.md](SECURITY.md) before connecting external systems. Destructive tool
use is disabled by policy, and demo mode is the default.

## Contributing

Issues and focused pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the development
workflow. This project is available under the [MIT License](LICENSE).
