import secrets

import pytest

from app.orchestration.engine import prepare_workflow
from app.orchestration.executor import execute_approved_actions
from app.orchestration.planner import RuleBasedClassifier
from app.state.models import ApprovalRecord, RunStatus, WorkflowRun


@pytest.mark.asyncio
async def test_execution_replay_does_not_duplicate_side_effects(repository, connectors):
    run = WorkflowRun(
        run_id="run-1", idempotency_key="idem-0001", requester="demo",
        title="Monthly commentary", raw_request="Automate monthly portfolio commentary drafting",
        approval_token_hash=secrets.token_hex(32),
    )
    repository.save(run)
    await prepare_workflow(run, connectors, RuleBasedClassifier(), repository)
    run.approval = ApprovalRecord(approved_by="owner")
    repository.transition(run, RunStatus.APPROVED)
    first = await execute_approved_actions(run, connectors, repository)
    # A client retry after completion reads the already-completed run rather than executing again.
    second = repository.get(run.run_id)
    assert first.status == second.status == RunStatus.COMPLETED
    assert first.artifacts["repository"] == second.artifacts["repository"]
    assert len(second.artifacts["issues"]) == 3


def test_effect_ledger_returns_original_result(repository):
    calls = 0
    def operation():
        nonlocal calls
        calls += 1
        return {"id": calls}
    first, created_first = repository.effect("same-action", "run", operation)
    second, created_second = repository.effect("same-action", "run", operation)
    assert first == second == {"id": 1}
    assert (created_first, created_second) == (True, False)
    assert calls == 1
