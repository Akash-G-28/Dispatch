from dataclasses import dataclass

from app.connectors.github_mcp import GitHubMCPConnector
from app.connectors.notion_mcp import NotionMCPConnector
from app.connectors.slack_mcp import SlackMCPConnector


@dataclass
class Connectors:
    github: GitHubMCPConnector
    notion: NotionMCPConnector
    slack: SlackMCPConnector


def demo_connectors() -> Connectors:
    return Connectors(GitHubMCPConnector(), NotionMCPConnector(), SlackMCPConnector())

