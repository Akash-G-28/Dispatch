from datetime import UTC, datetime

import pytest

from app.connectors.github_mcp import GitHubMCPConnector
from app.state.models import RunStatus, WorkflowRun
from app.state.transitions import validate_transition


@pytest.mark.asyncio
async def test_connector_rejects_write_without_approval():
    with pytest.raises(PermissionError):
        await GitHubMCPConnector().create_repo("test", "test", approved=False)


def test_state_machine_rejects_execution_before_approval():
    with pytest.raises(ValueError):
        validate_transition(RunStatus.PENDING_APPROVAL, RunStatus.EXECUTING)

