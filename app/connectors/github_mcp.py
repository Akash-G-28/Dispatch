from app.connectors.base import BaseConnector
from app.core.policies import assert_tool_allowed
from app.core.sentry_setup import traced


class GitHubMCPConnector(BaseConnector):
    name = "github"

    async def healthcheck(self) -> dict:
        return {"connector": self.name, "status": "demo"}

    async def create_repo(self, repo_name: str, description: str, *, approved: bool) -> dict:
        assert_tool_allowed("github.create_repo", approved=approved)
        with traced("connector.github", "Create starter repository"):
            return {"full_name": f"demo-org/{repo_name}", "url": f"https://github.com/demo-org/{repo_name}"}

    async def create_issue(self, repo: str, title: str, body: str, *, approved: bool) -> dict:
        assert_tool_allowed("github.create_issue", approved=approved)
        with traced("connector.github", "Create starter issue"):
            number = abs(hash((repo, title))) % 10000
            return {"number": number, "title": title, "url": f"https://github.com/{repo}/issues/{number}"}

