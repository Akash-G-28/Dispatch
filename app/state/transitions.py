from app.state.models import RunStatus


ALLOWED_TRANSITIONS = {
    RunStatus.RECEIVED: {RunStatus.CLASSIFIED, RunStatus.FAILED, RunStatus.CANCELLED},
    RunStatus.CLASSIFIED: {RunStatus.DRAFTED, RunStatus.FAILED, RunStatus.CANCELLED},
    RunStatus.DRAFTED: {RunStatus.PENDING_APPROVAL, RunStatus.EXECUTING, RunStatus.FAILED},
    RunStatus.PENDING_APPROVAL: {RunStatus.APPROVED, RunStatus.CANCELLED},
    RunStatus.APPROVED: {RunStatus.EXECUTING, RunStatus.CANCELLED},
    RunStatus.EXECUTING: {RunStatus.COMPLETED, RunStatus.FAILED},
    RunStatus.FAILED: {RunStatus.EXECUTING, RunStatus.CANCELLED},
    RunStatus.COMPLETED: set(),
    RunStatus.CANCELLED: set(),
}


def validate_transition(current: RunStatus, target: RunStatus) -> None:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"Invalid workflow transition: {current} -> {target}")

