import hashlib
import secrets
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas import CreateRunRequest, CreateRunResponse, ExecuteRequest
from app.connectors import Connectors
from app.orchestration.engine import prepare_workflow
from app.orchestration.executor import execute_approved_actions
from app.orchestration.planner import RuleBasedClassifier
from app.state.models import RunStatus, WorkflowRun
from app.state.repository import RunNotFoundError, SQLiteRunRepository

router = APIRouter(prefix="/runs")


def get_repository() -> SQLiteRunRepository:
    from app.main import repository
    return repository


def get_connectors() -> Connectors:
    from app.main import connectors
    return connectors


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@router.post(
    "",
    response_model=CreateRunResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["1. Request Intake"],
    summary="Submit and analyze an AI request",
    description=(
        "Creates a durable workflow run, classifies the business request, retrieves applicable "
        "demo standards, drafts a solution brief, and pauses at the human approval gate. Save the "
        "returned `run_id` and one-time `approval_token` for the next steps."
    ),
    operation_id="submit_ai_request",
)
async def create_run(
    request: CreateRunRequest,
    repository: SQLiteRunRepository = Depends(get_repository),
    connectors: Connectors = Depends(get_connectors),
) -> CreateRunResponse:
    existing = repository.get_by_idempotency_key(request.idempotency_key)
    if existing:
        return CreateRunResponse(run=existing)
    approval_token = secrets.token_urlsafe(32)
    run = WorkflowRun(
        run_id=str(uuid4()), approval_token_hash=token_hash(approval_token), **request.model_dump()
    )
    repository.save(run)
    repository.audit(run.run_id, "run_received", {"requester": run.requester})
    await prepare_workflow(run, connectors, RuleBasedClassifier(), repository)
    return CreateRunResponse(run=run, approval_token=approval_token)


@router.get(
    "/{run_id}",
    response_model=WorkflowRun,
    tags=["1. Request Intake"],
    summary="Inspect workflow status and artifacts",
    description=(
        "Returns the current state, classification, approval record, solution brief, and any "
        "delivery artifacts generated for a workflow run."
    ),
    operation_id="get_workflow_run",
)
async def get_run(run_id: str, repository: SQLiteRunRepository = Depends(get_repository)) -> WorkflowRun:
    try:
        return repository.get(run_id)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.post(
    "/{run_id}/execute",
    response_model=WorkflowRun,
    tags=["3. Approved Execution"],
    summary="Execute the approved delivery plan",
    description=(
        "Verifies the approval token and persisted approval record, then performs idempotent demo "
        "GitHub actions and publishes a demo Slack completion update. A run that has not been "
        "approved is rejected."
    ),
    operation_id="execute_approved_plan",
)
async def execute_run(
    run_id: str,
    request: ExecuteRequest,
    repository: SQLiteRunRepository = Depends(get_repository),
    connectors: Connectors = Depends(get_connectors),
) -> WorkflowRun:
    try:
        run = repository.get(run_id)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    if not run.approval_token_hash or not secrets.compare_digest(run.approval_token_hash, token_hash(request.approval_token)):
        raise HTTPException(status_code=403, detail="Invalid approval token")
    if run.status == RunStatus.COMPLETED:
        return run
    try:
        return await execute_approved_actions(run, connectors, repository)
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
