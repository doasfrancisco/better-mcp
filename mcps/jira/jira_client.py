"""Jira Cloud client — read-only wrapper around atlassian-python-api.

Gotchas worth knowing:

- Jira Cloud JQL needs a bounded query. A plain `ORDER BY created DESC` with no
  WHERE clause is rejected with "Aquí no se permiten las consultas JQL
  ilimitadas" / "Unbounded JQL queries are not allowed here." Every search must
  include at least one filter clause (project = X, created >= -30d,
  assignee = currentUser(), status = "Open", etc.). The server instructions
  and tool docstring repeat this, but enforce it at the call site too if the
  query starts with ORDER BY — see `search_issues` below.

- `cloud=True` is required when talking to *.atlassian.net. The API token goes
  in `password`, NOT in the `token` parameter (that one is for Data Center PATs).

- The library exposes two naming conventions: `issue_get_*` (newer) and
  `get_issue_*` (older). Both are on the class; we use whichever exists.
"""

import os
from pathlib import Path
from typing import Any, Optional

from atlassian import Jira
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

_URL = os.getenv("JIRA_URL")
_EMAIL = os.getenv("JIRA_EMAIL")
_TOKEN = os.getenv("JIRA_API_TOKEN")

if not (_URL and _EMAIL and _TOKEN):
    raise RuntimeError("Missing JIRA_URL / JIRA_EMAIL / JIRA_API_TOKEN in .env")

# Cloud=True is mandatory for *.atlassian.net. Token goes in `password`.
_jira = Jira(url=_URL, username=_EMAIL, password=_TOKEN, cloud=True)


# ---------- helpers ----------

def slim_issue(iss: dict) -> dict:
    """Flatten a Jira issue payload down to fields that matter for AI clients."""
    f = iss.get("fields", {}) or {}
    status = f.get("status") or {}
    priority = f.get("priority") or {}
    issuetype = f.get("issuetype") or {}
    assignee = f.get("assignee") or {}
    reporter = f.get("reporter") or {}
    parent = f.get("parent") or {}
    return {
        "key": iss.get("key"),
        "id": iss.get("id"),
        "summary": f.get("summary"),
        "status": status.get("name"),
        "status_category": (status.get("statusCategory") or {}).get("key"),
        "priority": priority.get("name"),
        "issuetype": issuetype.get("name"),
        "assignee": assignee.get("displayName"),
        "assignee_account_id": assignee.get("accountId"),
        "reporter": reporter.get("displayName"),
        "created": f.get("created"),
        "updated": f.get("updated"),
        "resolution": (f.get("resolution") or {}).get("name"),
        "labels": f.get("labels"),
        "parent": parent.get("key") if parent else None,
        "project": (f.get("project") or {}).get("key"),
        "description": f.get("description"),
    }


# ---------- issues ----------

def search_issues(
    jql: str,
    fields: str = "summary,status,priority,issuetype,assignee,reporter,created,updated,resolution,labels,project,parent",
    limit: int = 25,
    start: int = 0,
    expand: Optional[str] = None,
    slim: bool = True,
) -> dict:
    # Fail fast on unbounded queries — Jira Cloud rejects them with a 400
    # wrapped in a cryptic Spanish error. Do the check here so the AI client
    # gets a clear message instead.
    stripped = jql.strip().lower()
    if not stripped or stripped.startswith("order by"):
        raise ValueError(
            "Jira Cloud rejects unbounded JQL. Add at least one filter clause "
            "(e.g. project = X, created >= -30d, assignee = currentUser()) "
            "before any ORDER BY."
        )

    result = _jira.jql(jql, fields=fields, start=start, limit=limit, expand=expand) or {}
    issues = result.get("issues", []) or []
    return {
        "total": result.get("total"),
        "startAt": result.get("startAt"),
        "maxResults": result.get("maxResults"),
        "issues": [slim_issue(i) for i in issues] if slim else issues,
    }


def get_issue(key: str, fields: str = "*all", expand: Optional[str] = "renderedFields,names,schema", slim: bool = False) -> Any:
    iss = _jira.issue(key, fields=fields, expand=expand)
    return slim_issue(iss) if slim else iss


def get_issue_changelog(key: str, start: int = 0, limit: int = 50) -> Any:
    return _jira.get_issue_changelog(key, start=start, limit=limit)


def get_issue_transitions(key: str) -> Any:
    return _jira.get_issue_transitions(key)


def get_issue_status_changelog(key: str) -> Any:
    return _jira.get_issue_status_changelog(key)


def get_issue_comments(key: str) -> Any:
    return _jira.issue_get_comments(key)


def get_issue_worklog(key: str) -> Any:
    return _jira.issue_get_worklog(key)


def get_issue_watchers(key: str) -> Any:
    return _jira.issue_get_watchers(key)


def get_issue_attachments(key: str) -> Any:
    return _jira.get_attachments_ids_from_issue(key)


def get_attachment(attachment_id: str) -> Any:
    return _jira.get_attachment(attachment_id)


# ---------- projects ----------

def list_projects(expand: Optional[str] = None) -> Any:
    return _jira.projects(expand=expand)


def get_project(key: str) -> Any:
    return _jira.project(key)


def get_project_components(key: str) -> Any:
    return _jira.get_project_components(key)


def get_project_versions(key: str) -> Any:
    return _jira.get_project_versions(key)


def get_project_issue_count(key: str) -> Any:
    return _jira.get_project_issues_count(key)


# ---------- users ----------

def search_users(query: str, start: int = 0, limit: int = 25) -> Any:
    return _jira.user_find_by_user_string(query=query, start=start, limit=limit)


def get_myself() -> Any:
    return _jira.myself()


# ---------- agile ----------

def list_boards(
    board_name: Optional[str] = None,
    project_key: Optional[str] = None,
    board_type: Optional[str] = None,
    start: int = 0,
    limit: int = 50,
) -> Any:
    return _jira.get_all_agile_boards(
        board_name=board_name,
        project_key=project_key,
        board_type=board_type,
        start=start,
        limit=limit,
    )


def list_board_sprints(board_id: int, state: Optional[str] = None, start: int = 0, limit: int = 50) -> Any:
    return _jira.get_all_sprints_from_board(board_id, state=state, start=start, limit=limit)


def get_sprint_issues(
    board_id: int,
    sprint_id: int,
    jql: str = "",
    fields: str = "summary,status,assignee,priority",
    start: int = 0,
    limit: int = 50,
) -> Any:
    return _jira.get_all_issues_for_sprint_in_board(
        board_id=board_id,
        sprint_id=sprint_id,
        jql=jql,
        fields=fields,
        start=start,
        limit=limit,
    )


# ---------- metadata ----------

def list_fields() -> Any:
    return _jira.get_all_fields()


def list_statuses() -> Any:
    return _jira.get_all_statuses()


def list_priorities() -> Any:
    return _jira.get_all_priorities()
