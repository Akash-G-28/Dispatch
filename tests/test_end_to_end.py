import hashlib
import secrets

import pytest

from app.orchestration.engine import prepare_workflow
from app.orchestration.executor import execute_approved_actions
from app.orchestration.planner import RuleBasedClassifier
from app.state.models import ApprovalRecord, RunStatus, WorkflowRun


@pytest.mark.asyncio
async def test_full_demo_flow(repository, connectors):
    token = secrets.token_urlsafe(32)
    run = WorkflowRun(
        run_id="demo-run", idempotency_key="demo-key-123", requester="business-owner",
        title="Exposure commentary automation",
        raw_request="Can AI help automate monthly exposure commentary generation?",
        approval_token_hash=hashlib.sha256(token.encode()).hexdigest(),
    )
    repository.save(run)
    prepared = await prepare_workflow(run, connectors, RuleBasedClassifier(), repository)
    assert prepared.status == RunStatus.PENDING_APPROVAL
    assert "Solution Brief" in prepared.artifacts["solution_brief"]
    prepared.approval = ApprovalRecord(approved_by="control-owner")
    repository.transition(prepared, RunStatus.APPROVED)
    completed = await execute_approved_actions(prepared, connectors, repository)
    assert completed.status == RunStatus.COMPLETED
    assert len(completed.artifacts["issues"]) == 3
    assert completed.artifacts["slack_update"]["channel"]

