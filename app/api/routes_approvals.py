import secrets

from fastapi import APIRouter, Depends, HTTPException

from app.api.routes_runs import get_repository, token_hash
from app.api.schemas import ApprovalRequest
from app.state.models import ApprovalRecord, RunStatus, WorkflowRun
from app.state.repository import RunNotFoundError, SQLiteRunRepository

router = APIRouter(prefix="/runs")


@router.post(
    "/{run_id}/approve",
    response_model=WorkflowRun,
    tags=["2. Human Approval"],
    summary="Approve the proposed delivery plan",
    description=(
        "Records the named approver and reason after verifying the one-time token returned when "
        "the run was created. This moves the workflow from `PENDING_APPROVAL` to `APPROVED`; it "
        "does not execute external actions yet."
    ),
    operation_id="approve_delivery_plan",
)
async def approve_run(
    run_id: str,
    request: ApprovalRequest,
    repository: SQLiteRunRepository = Depends(get_repository),
) -> WorkflowRun:
    try:
        run = repository.get(run_id)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    if run.status != RunStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=409, detail="Run is not pending approval")
    if not run.approval_token_hash or not secrets.compare_digest(run.approval_token_hash, token_hash(request.approval_token)):
        raise HTTPException(status_code=403, detail="Invalid approval token")
    run.approval = ApprovalRecord(approved_by=request.approved_by, reason=request.reason)
    repository.transition(run, RunStatus.APPROVED, {"approved_by": request.approved_by})
    return run
