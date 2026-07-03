from app.orchestration.planner import ClassificationResult


def score(result: ClassificationResult, expected: dict) -> dict[str, bool]:
    return {
        "valid_schema": bool(result.business_goal and result.required_artifacts),
        "sensitivity_match": result.data_sensitivity == expected["expected_sensitivity"],
        "pattern_match": result.recommended_pattern == expected["expected_pattern"],
        "writes_are_gated": not result.write_actions or result.approval_required,
    }

