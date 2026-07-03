from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(UTC)


class RunStatus(StrEnum):
    RECEIVED = "RECEIVED"
    CLASSIFIED = "CLASSIFIED"
    DRAFTED = "DRAFTED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ApprovalRecord(BaseModel):
    approved_by: str
    approved_at: datetime = Field(default_factory=utcnow)
    decision: str = "approved"
    reason: str | None = None


class WorkflowRun(BaseModel):
    run_id: str
    idempotency_key: str
    requester: str
    title: str
    raw_request: str
    status: RunStatus = RunStatus.RECEIVED
    classification: dict[str, Any] = Field(default_factory=dict)
    artifacts: dict[str, Any] = Field(default_factory=dict)
    pending_write_actions: list[str] = Field(default_factory=list)
    approval: ApprovalRecord | None = None
    approval_token_hash: str | None = Field(default=None, exclude=True)
    error: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

