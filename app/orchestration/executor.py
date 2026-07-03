import re

from app.connectors import Connectors
from app.state.models import RunStatus, WorkflowRun
from app.state.repository import SQLiteRunRepository


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:60] or "ai-delivery-project"


async def execute_approved_actions(
    run: WorkflowRun, connectors: Connectors, repository: SQLiteRunRepository
) -> WorkflowRun:
    if run.status not in {RunStatus.APPROVED, RunStatus.FAILED} or not run.approval:
        raise PermissionError("Run must have a verified approval before execution")
    repository.transition(run, RunStatus.EXECUTING)
    try:
        repo_name = _slug(run.title)
        repo_result, _ = repository.effect(
            f"{run.run_id}:github:create_repo:{repo_name}", run.run_id,
            lambda: {"full_name": f"demo-org/{repo_name}", "url": f"https://github.com/demo-org/{repo_name}"},
        )
        # The connector enforces policy and emits the trace; the durable effect ledger owns replay safety.
        await connectors.github.create_repo(repo_name, run.raw_request, approved=True)
        issues = []
        for title in ("Validate use case and data controls", "Build approval-gated workflow", "Add evaluation and observability"):
            action_key = f"{run.run_id}:github:create_issue:{_slug(title)}"
            cached, created = repository.effect(
                action_key, run.run_id,
                lambda title=title: {"number": abs(hash((repo_result["full_name"], title))) % 10000, "title": title},
            )
            if created:
                traced_result = await connectors.github.create_issue(repo_result["full_name"], title, "Starter delivery task", approved=True)
                cached.update(traced_result)
            issues.append(cached)
        run.artifacts.update({"repository": repo_result, "issues": issues})
        repository.transition(run, RunStatus.COMPLETED)
        slack = await connectors.slack.send_status(
            f"Run {run.run_id} completed: {repo_result['url']}", state_changed=True
        )
        run.artifacts["slack_update"] = slack
        repository.save(run)
        return run
    except Exception as exc:
        run.error = str(exc)
        repository.transition(run, RunStatus.FAILED)
        raise
