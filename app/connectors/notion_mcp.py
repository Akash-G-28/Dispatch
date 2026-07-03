from app.connectors.base import BaseConnector
from app.core.policies import assert_tool_allowed
from app.core.sentry_setup import traced


class NotionMCPConnector(BaseConnector):
    name = "notion"

    async def healthcheck(self) -> dict:
        return {"connector": self.name, "status": "demo"}

    async def get_relevant_standards(self, use_case_type: str) -> list[dict]:
        assert_tool_allowed("notion.search")
        with traced("connector.notion", "Retrieve relevant standards"):
            return [
                {"title": "Human approval for external side effects", "source": "demo://notion/approval"},
                {"title": "Sensitive data handling and prompt minimization", "source": "demo://notion/data"},
                {"title": f"Delivery pattern: {use_case_type}", "source": "demo://notion/pattern"},
            ]

