from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = "sqlite:///./workflow.db"
    sentry_dsn: str = ""
    github_mcp_url: str = "https://api.githubcopilot.com/mcp/"
    github_token: str = ""
    notion_mcp_url: str = "https://mcp.notion.com/mcp"
    notion_token: str = ""
    slack_mcp_url: str = "https://mcp.slack.com/mcp"
    slack_bot_token: str = ""
    enable_playwright: bool = False
    connector_mode: str = "demo"


@lru_cache
def get_settings() -> Settings:
    return Settings()

