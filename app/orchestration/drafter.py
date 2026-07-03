from app.orchestration.planner import ClassificationResult
from app.state.models import WorkflowRun


async def draft_solution_brief(
    run: WorkflowRun, classification: ClassificationResult, standards: list[dict]
) -> str:
    standards_text = "; ".join(item["title"] for item in standards) or "No matching standards"
    return f"""# Solution Brief: {run.title}

## Problem statement
{run.raw_request}

## Target users
Business domain owners, AI enablement engineers, delivery managers, and control partners.

## Expected business outcome
Reduce request-to-draft cycle time while retaining human accountability for delivery actions.

## Recommended architecture pattern
{classification.recommended_pattern.title()} with persistent state and approval-gated execution.

## Data and security considerations
Sensitivity: **{classification.data_sensitivity}**. Apply least privilege, redact sensitive prompt data,
retain an audit trail, and prohibit writes until an explicit approval token is verified.

## Applicable internal standards
{standards_text}

## Success metrics
- Solution brief turnaround under 60 seconds
- Zero duplicate side effects under retry
- 100% of write actions explicitly approved
- Complete trace and audit record for every run

## First implementation milestone
Validate classification and brief quality on curated examples, then bootstrap a repository and three
issues in demo mode.
"""

