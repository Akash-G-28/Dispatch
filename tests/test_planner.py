import pytest

from app.orchestration.planner import RuleBasedClassifier


@pytest.mark.asyncio
async def test_portfolio_commentary_is_high_sensitivity_and_gated():
    result = await RuleBasedClassifier().classify(
        "Automate monthly portfolio commentary from internal analyst notes"
    )
    assert result.data_sensitivity == "HIGH"
    assert result.approval_required is True
    assert result.recommended_pattern == "workflow automation"

