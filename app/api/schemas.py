from pydantic import BaseModel, Field

from app.state.models import WorkflowRun


class CreateRunRequest(BaseModel):
    requester: str = Field(
        min_length=1,
        description="Person or team submitting the business request.",
        examples=["Akash"],
    )
    title: str = Field(
        min_length=1,
        max_length=120,
        description="Short, human-readable name for this workflow.",
        examples=["Monthly exposure commentary"],
    )
    raw_request: str = Field(
        min_length=10,
        description="The original business problem or AI opportunity to assess.",
        examples=["Can AI help automate monthly exposure commentary generation?"],
    )
    idempotency_key: str = Field(
        min_length=8,
        max_length=200,
        description="Client-generated unique key that prevents duplicate workflow runs on retries.",
        examples=["exposure-commentary-2026-07-04-001"],
    )


class CreateRunResponse(BaseModel):
    run: WorkflowRun
    approval_token: str | None = None


class ApprovalRequest(BaseModel):
    approved_by: str = Field(
        min_length=1,
        description="Name or identifier of the human accepting responsibility for the decision.",
        examples=["Akash"],
    )
    approval_token: str = Field(
        min_length=20,
        description="One-time token returned by the original POST /runs response.",
    )
    reason: str | None = Field(
        default=None,
        description="Optional explanation, constraint, or evidence supporting the decision.",
        examples=["Approved for controlled demo execution."],
    )


class ExecuteRequest(BaseModel):
    approval_token: str = Field(
        min_length=20,
        description="The same token used to approve the workflow run.",
    )
