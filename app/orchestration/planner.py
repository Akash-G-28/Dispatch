from typing import Protocol

from pydantic import BaseModel


class ClassificationResult(BaseModel):
    use_case_type: str
    business_goal: str
    data_sensitivity: str
    required_artifacts: list[str]
    write_actions: list[str]
    recommended_pattern: str
    approval_required: bool
    rationale: str
    value_score: int
    complexity_score: int
    risk_score: int


class Classifier(Protocol):
    async def classify(self, request: str) -> ClassificationResult: ...


class RuleBasedClassifier:
    """Deterministic local classifier; replace with a structured-output LLM adapter."""

    async def classify(self, request: str) -> ClassificationResult:
        text = request.lower()
        sensitive = any(word in text for word in ("client", "trade", "portfolio", "pii", "exposure"))
        workflow = any(word in text for word in ("automate", "monthly", "workflow", "commentary"))
        return ClassificationResult(
            use_case_type="document_generation" if "commentary" in text else "workflow_automation",
            business_goal=request.strip(),
            data_sensitivity="HIGH" if sensitive else "MEDIUM",
            required_artifacts=["solution_brief", "architecture_note", "implementation_checklist"],
            write_actions=["github.create_repo", "github.create_issue", "slack.send_message"],
            recommended_pattern="workflow automation" if workflow else "document intelligence",
            approval_required=True,
            rationale="Creates delivery artifacts and may process regulated business data.",
            value_score=8 if workflow else 6,
            complexity_score=6,
            risk_score=8 if sensitive else 5,
        )

