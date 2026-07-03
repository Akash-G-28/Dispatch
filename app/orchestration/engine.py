from app.connectors import Connectors
from app.orchestration.drafter import draft_solution_brief
from app.orchestration.planner import Classifier
from app.state.models import RunStatus, WorkflowRun
from app.state.repository import SQLiteRunRepository


async def prepare_workflow(
    run: WorkflowRun, connectors: Connectors, classifier: Classifier, repository: SQLiteRunRepository
) -> WorkflowRun:
    repository.transition(run, RunStatus.CLASSIFIED)
    classification = await classifier.classify(run.raw_request)
    run.classification = classification.model_dump()
    run.pending_write_actions = classification.write_actions
    repository.save(run)

    standards = await connectors.notion.get_relevant_standards(classification.use_case_type)
    repository.transition(run, RunStatus.DRAFTED)
    run.artifacts["standards"] = standards
    run.artifacts["solution_brief"] = await draft_solution_brief(run, classification, standards)
    repository.save(run)
    repository.transition(run, RunStatus.PENDING_APPROVAL)
    return run

