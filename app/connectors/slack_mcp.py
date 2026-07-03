from app.connectors.base import BaseConnector
from app.core.policies import assert_tool_allowed
from app.core.sentry_setup import traced


class SlackMCPConnector(BaseConnector):
    name = "slack"

    async def healthcheck(self) -> dict:
        return {"connector": self.name, "status": "demo"}

    async def send_status(self, message: str, *, state_changed: bool) -> dict:
        assert_tool_allowed("slack.send_message", state_changed=state_changed)
        with traced("connector.slack", "Publish workflow status"):
            return {"channel": "demo-ai-delivery", "ts": "demo", "message": message}
