# Contributing

Thanks for helping improve AI Delivery Control Plane.

## Development setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m pytest
```

Keep changes focused and include tests for behavior changes. External writes must remain approval-gated,
idempotent, and observable. Never add real credentials or sensitive business data to fixtures.

## Pull requests

1. Explain the user or operational problem.
2. Describe the behavior change and its risk.
3. Add or update tests.
4. Confirm `python -m pytest` passes.
5. Call out any new connector permissions or side effects explicitly.
