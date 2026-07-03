# Security Policy

## Supported versions

This project is currently an alpha reference implementation. Security fixes target the latest revision
on the default branch.

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub's **Security → Report a vulnerability** flow.
Do not open a public issue containing credentials, sensitive data, or exploit details.

## Deployment notes

- Demo connectors return synthetic results and are not production MCP transports.
- Store secrets outside the repository and rotate any credential that is accidentally committed.
- Add authentication and authorization before exposing the API beyond localhost.
- Use Postgres with concurrency controls for multi-worker deployments.
- Give connectors least-privilege credentials and retain the approval and idempotency controls.
- Avoid sending raw sensitive requests to logs, traces, or third-party model providers.
