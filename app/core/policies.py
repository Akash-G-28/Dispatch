from enum import StrEnum


class ToolPermission(StrEnum):
    READ = "read"
    APPROVAL_REQUIRED = "approval_required"
    ALLOWED_AFTER_STATE_CHANGE = "allowed_after_state_change"
    DISABLED = "disabled"


TOOL_POLICY = {
    "github.read_repo": ToolPermission.READ,
    "github.create_repo": ToolPermission.APPROVAL_REQUIRED,
    "github.create_issue": ToolPermission.APPROVAL_REQUIRED,
    "notion.search": ToolPermission.READ,
    "notion.create_page": ToolPermission.APPROVAL_REQUIRED,
    "slack.send_message": ToolPermission.ALLOWED_AFTER_STATE_CHANGE,
    "playwright.browser_run_code_unsafe": ToolPermission.DISABLED,
}


def assert_tool_allowed(tool: str, *, approved: bool = False, state_changed: bool = False) -> None:
    permission = TOOL_POLICY.get(tool, ToolPermission.DISABLED)
    if permission == ToolPermission.DISABLED:
        raise PermissionError(f"Tool is disabled: {tool}")
    if permission == ToolPermission.APPROVAL_REQUIRED and not approved:
        raise PermissionError(f"Explicit approval required: {tool}")
    if permission == ToolPermission.ALLOWED_AFTER_STATE_CHANGE and not state_changed:
        raise PermissionError(f"State change required before tool call: {tool}")

