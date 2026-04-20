"""Jira MCP server — thin FastMCP wrappers over jira_client.

All tools are READ-ONLY. Business logic and library gotchas live in
jira_client.py.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional

from fastmcp import FastMCP

import jira_client as j

_log_dir = Path(__file__).parent / "logs"
_log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.WARNING,
    handlers=[RotatingFileHandler(_log_dir / "server.log", maxBytes=5_000_000, backupCount=1)],
)

mcp = FastMCP(
    "Jira",
    instructions="""This server reads from a Jira Cloud instance (configured via JIRA_URL in .env).

All tools are READ-ONLY. No writes, comments, transitions, or edits are exposed.

When the user asks about "tickets", "issues", or "tasks" — use jira_search_issues with JQL.
Jira Cloud requires a bounded JQL query — always include at least one constraint
(project = X, created >= -30d, assignee = currentUser(), status = "Open", etc.)
before any ORDER BY.

When presenting issues, format as:
  [STATUS] KEY-123 Summary (assignee · YYYY-MM-DD)
""",
)


# ---------- issues ----------

@mcp.tool
def jira_search_issues(
    jql: str,
    fields: str = "summary,status,priority,issuetype,assignee,reporter,created,updated,resolution,labels,project,parent",
    limit: int = 25,
    start: int = 0,
    expand: Optional[str] = None,
    slim: bool = True,
) -> dict:
    """Search Jira issues with JQL. Must include at least one filter clause."""
    return j.search_issues(jql, fields=fields, limit=limit, start=start, expand=expand, slim=slim)


@mcp.tool
def jira_get_issue(
    key: str,
    fields: str = "*all",
    expand: Optional[str] = "renderedFields,names,schema",
    slim: bool = False,
) -> Any:
    """Get a single Jira issue by key (e.g. APM-720)."""
    return j.get_issue(key, fields=fields, expand=expand, slim=slim)


@mcp.tool
def jira_get_issue_changelog(key: str, start: int = 0, limit: int = 50) -> Any:
    """Get the field-change audit history for an issue."""
    return j.get_issue_changelog(key, start=start, limit=limit)


@mcp.tool
def jira_get_issue_transitions(key: str) -> Any:
    """List the workflow transitions currently available for an issue (read only)."""
    return j.get_issue_transitions(key)


@mcp.tool
def jira_get_issue_status_changelog(key: str) -> Any:
    """Get a cleaned status-transition history for an issue."""
    return j.get_issue_status_changelog(key)


@mcp.tool
def jira_get_issue_comments(key: str) -> Any:
    """Get all comments on an issue."""
    return j.get_issue_comments(key)


@mcp.tool
def jira_get_issue_worklog(key: str) -> Any:
    """Get all worklog entries for an issue."""
    return j.get_issue_worklog(key)


@mcp.tool
def jira_get_issue_watchers(key: str) -> Any:
    """Get the list of watchers for an issue."""
    return j.get_issue_watchers(key)


@mcp.tool
def jira_get_issue_attachments(key: str) -> Any:
    """List attachments on an issue (id + filename)."""
    return j.get_issue_attachments(key)


@mcp.tool
def jira_get_attachment(attachment_id: str) -> Any:
    """Get metadata for a single attachment (mime type, size, URL)."""
    return j.get_attachment(attachment_id)


# ---------- projects ----------

@mcp.tool
def jira_list_projects(expand: Optional[str] = None) -> Any:
    """List all projects visible to the authenticated user."""
    return j.list_projects(expand=expand)


@mcp.tool
def jira_get_project(key: str) -> Any:
    """Get full project metadata by key (e.g. APM)."""
    return j.get_project(key)


@mcp.tool
def jira_get_project_components(key: str) -> Any:
    """List components for a project."""
    return j.get_project_components(key)


@mcp.tool
def jira_get_project_versions(key: str) -> Any:
    """List versions/releases for a project."""
    return j.get_project_versions(key)


@mcp.tool
def jira_get_project_issue_count(key: str) -> Any:
    """Get the total count of issues in a project."""
    return j.get_project_issue_count(key)


# ---------- users ----------

@mcp.tool
def jira_search_users(query: str, start: int = 0, limit: int = 25) -> Any:
    """Search users by display name or email."""
    return j.search_users(query, start=start, limit=limit)


@mcp.tool
def jira_get_myself() -> Any:
    """Get the currently authenticated user (accountId, email, timezone)."""
    return j.get_myself()


# ---------- agile / boards ----------

@mcp.tool
def jira_list_boards(
    board_name: Optional[str] = None,
    project_key: Optional[str] = None,
    board_type: Optional[str] = None,
    start: int = 0,
    limit: int = 50,
) -> Any:
    """List agile boards (scrum/kanban)."""
    return j.list_boards(
        board_name=board_name,
        project_key=project_key,
        board_type=board_type,
        start=start,
        limit=limit,
    )


@mcp.tool
def jira_list_board_sprints(
    board_id: int,
    state: Optional[str] = None,
    start: int = 0,
    limit: int = 50,
) -> Any:
    """List sprints on a board. state = active | closed | future."""
    return j.list_board_sprints(board_id, state=state, start=start, limit=limit)


@mcp.tool
def jira_get_sprint_issues(
    board_id: int,
    sprint_id: int,
    jql: str = "",
    fields: str = "summary,status,assignee,priority",
    start: int = 0,
    limit: int = 50,
) -> Any:
    """Get all issues in a sprint for a given board."""
    return j.get_sprint_issues(
        board_id=board_id,
        sprint_id=sprint_id,
        jql=jql,
        fields=fields,
        start=start,
        limit=limit,
    )


# ---------- metadata ----------

@mcp.tool
def jira_list_fields() -> Any:
    """List all fields (system + custom). Useful for resolving custom field IDs."""
    return j.list_fields()


@mcp.tool
def jira_list_statuses() -> Any:
    """List all issue statuses across the instance."""
    return j.list_statuses()


@mcp.tool
def jira_list_priorities() -> Any:
    """List all issue priorities."""
    return j.list_priorities()


if __name__ == "__main__":
    mcp.run()
