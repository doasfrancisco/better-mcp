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

jira_get_issue returns the full ticket in one call: base fields + changelog +
status history + comments + worklog + watchers + attachments + available
transitions. Don't fan out into multiple sub-calls — everything is inlined.

jira_get_project returns project metadata + components + versions + issue count
in one call.

jira_list_metadata returns all fields (system + custom) + statuses + priorities
in one call — use it to resolve custom field IDs or status names before JQL.

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
    next_page_token: Optional[str] = None,
    expand: Optional[str] = None,
    slim: bool = True,
) -> dict:
    """Search Jira issues with JQL. Must include at least one filter clause
    (Cloud rejects unbounded queries). Returns {isLast, nextPageToken, issues}.
    To fetch the next page, pass the nextPageToken from the previous response."""
    return j.search_issues(jql, fields=fields, limit=limit, next_page_token=next_page_token, expand=expand, slim=slim)


@mcp.tool
def jira_get_issue(key: str) -> dict:
    """One-shot ticket view for a key (e.g. APM-720). Returns a dict with:
    issue (full fields), changelog, status_changelog, comments, worklog,
    watchers, attachments (list), transitions. No flags — always everything."""
    return j.get_issue_full(key)


@mcp.tool
def jira_get_attachment(attachment_id: str) -> Any:
    """Get metadata for a single attachment by ID (mime type, size, URL)."""
    return j.get_attachment(attachment_id)


# ---------- projects ----------

@mcp.tool
def jira_list_projects(expand: Optional[str] = None) -> Any:
    """List all projects visible to the authenticated user."""
    return j.list_projects(expand=expand)


@mcp.tool
def jira_get_project(key: str) -> dict:
    """One-shot project view for a key (e.g. APM). Returns a dict with:
    project (metadata), components, versions, issue_count. No flags."""
    return j.get_project_full(key)


# ---------- users ----------

@mcp.tool
def jira_search_users(query: str, start: int = 0, limit: int = 25) -> Any:
    """Search users by display name or email."""
    return j.search_users(query, start=start, limit=limit)


@mcp.tool
def jira_get_myself() -> Any:
    """Get the currently authenticated user — includes accountId, email,
    timezone, locale, group memberships (names), and application roles."""
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
def jira_list_metadata() -> dict:
    """One-shot instance metadata dump. Returns a dict with:
    fields (all system + custom), statuses, priorities. No flags."""
    return j.list_metadata()


if __name__ == "__main__":
    mcp.run()
