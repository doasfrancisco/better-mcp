# Jira read API reference — atlassian-python-api

Source: [`atlassian-api/atlassian-python-api`](https://github.com/atlassian-api/atlassian-python-api) (indexed on Nia, verified against `atlassian/jira.py`).

The MCP server in this folder wraps only the **read** subset of this library. Any method that creates/updates/deletes/transitions is deliberately **not** exposed.

Instantiation for Jira Cloud:

```python
from atlassian import Jira
jira = Jira(
    url="https://<your-domain>.atlassian.net",
    username="email@example.com",
    password="<API token>",
    cloud=True,
)
```

---

## Issues

| Method | Description |
|---|---|
| `issue(key, fields="*all", expand=None)` | Short-form get by key |
| `get_issue(issue_id_or_key, fields=None, properties=None, update_history=True, expand=None)` | Full issue representation |
| `get_issue_changelog(issue_key, start=None, limit=None)` | Field-change audit history |
| `get_issue_status(issue_key)` | Current status name |
| `get_issue_status_id(issue_key)` | Current status ID |
| `get_issue_status_changelog(issue_id)` | Cleaned status-transition history |
| `get_issue_transitions(issue_key)` | Workflow transitions currently available |
| `get_issue_labels(issue_key)` | Labels on an issue |

## Search / JQL

| Method | Description |
|---|---|
| `jql(jql, fields="*all", start=0, limit=None, expand=None)` | Standard JQL search |
| `enhanced_jql(jql, fields="*all", nextPageToken=None, limit=None, expand=None)` | Cloud-only paginated JQL (new API) |
| `approximate_issue_count(jql)` | Cloud-only fast count |
| `get_autocomplete_data()` | Autocomplete metadata for JQL builder |
| `export_html(jql, limit=None, all_fields=True, start=None)` | Export search to HTML file |

Cloud **rejects unbounded queries** — every JQL must have at least one filter (`project = X`, `created >= -30d`, `assignee = currentUser()`, etc).

## Comments

| Method | Description |
|---|---|
| `issue_get_comments(issue_id)` | All comments on an issue |
| `issue_get_comment(issue_id, comment_id)` | A single comment |
| `get_comment_properties_keys(comment_id)` | Keys of comment properties |
| `get_comment_property(comment_id, property_key)` | Value of a comment property |

## Worklog

| Method | Description |
|---|---|
| `issue_get_worklog(issue_id_or_key)` | All worklog entries for an issue |

## Watchers

| Method | Description |
|---|---|
| `issue_get_watchers(issue_key)` | Watchers on an issue |

## Attachments

| Method | Description |
|---|---|
| `get_attachments_ids_from_issue(issue)` | List of `{filename, attachment_id}` for the issue |
| `get_attachment(attachment_id)` | Metadata for an attachment (size, MIME, URI) |
| `get_attachment_content(attachment_id)` | Binary content of an attachment |
| `get_attachment_meta()` | Global upload limits / enabled flag |

## Projects

| Method | Description |
|---|---|
| `projects(included_archived=None, expand=None)` | List projects visible to the caller |
| `projects_from_cloud(included_archived=None, expand=None)` | Cloud-specific variant |
| `project(key)` | Project metadata by key |
| `project_leaders()` | Generator of project leaders |
| `get_project_components(key)` | Components for a project |
| `get_project_versions(key, expand=None)` | Versions/releases for a project |
| `get_project_versions_paginated(key, start=None, limit=None, ...)` | Paginated versions |
| `get_project_issuekey_last(project)` | Most recent issue key in a project |
| `get_project_issuekey_all(project, start=0, limit=None, expand=None)` | All issue keys |
| `get_project_issues_count(project)` | Total issue count for a project |
| `get_all_project_issues(project, fields="*all", start=0, limit=None)` | Dump all issues in a project |

## Users

| Method | Description |
|---|---|
| `myself()` | Currently authenticated user |
| `user(username, expand=None)` | Look up a user |
| `user_find_by_user_string(username=None, query=None, start=0, limit=50)` | Search users by name/email |
| `get_users_with_browse_permission_to_a_project(username, issue_key=None, project_key=None, start=0, limit=100)` | Users who can browse project/issue |

## Fields (system + custom)

| Method | Description |
|---|---|
| `get_all_fields()` | All fields — system and custom |
| `get_custom_fields(search=None, start=1, limit=50)` | Paginated custom-field search |
| `get_all_custom_fields()` | All custom fields |

## Metadata (statuses, priorities, etc.)

| Method | Description |
|---|---|
| `get_all_statuses()` | All issue statuses |
| `get_all_priorities()` | All priorities |
| `get_priority_by_id(priority_id)` | One priority by ID |

## Agile / Boards / Sprints

| Method | Description |
|---|---|
| `get_all_agile_boards(board_name=None, project_key=None, board_type=None, start=0, limit=50)` | List agile boards |
| `get_agile_board_by_filter_id(filter_id)` | Resolve board by filter |
| `get_board_configuration(board_id)` | Columns, filter, estimation/ranking field |
| `get_issues_for_board(board_id, jql, fields="*all", start=0, limit=None, expand=None)` | Issues on a board (JQL-filtered) |
| `get_all_sprints_from_board(board_id, state=None, start=0, limit=None)` | Sprints on a board |
| `get_sprints_from_board(...)` | Alias of above |
| `get_all_issues_for_sprint_in_board(board_id, sprint_id, jql="", validateQuery=True, fields="", expand="", start=0, limit=50)` | Issues in a sprint |
| `get_all_versions_from_board(board_id, released="true", start=0, limit=50)` | Versions on a board |

## Permissions

| Method | Description |
|---|---|
| `get_permissions(permissions, project_id=None, project_key=None, issue_id=None, issue_key=None)` | What the current user can do in a scope |
| `get_all_permissions()` | All permissions defined in the instance |

## Application / system

| Method | Description |
|---|---|
| `get_property(key=None, permission_level=None, key_filter=None)` | Application properties |
| `get_advanced_settings()` | General Configuration → Advanced Settings |
| `get_all_application_roles()` | All application roles |
| `get_application_role(role_key)` | One role |

## Create metadata (read-only view, despite the name)

| Method | Description |
|---|---|
| `issue_createmeta(project, expand="projects.issuetypes.fields")` | **Deprecated** — legacy create metadata |
| `issue_createmeta_issuetypes(project, start=None, limit=None)` | Issue types available in a project |
| `issue_createmeta_fieldtypes(project, issue_type_id, start=None, limit=None)` | Fields required/allowed per issue type |
| `issue_editmeta(key)` | Fields editable on a given issue |

---

## What the MCP server exposes

The server bundles related reads into composed tools so the AI gets everything
it needs in one call instead of fanning out into 5+ round-trips.

| Tool | Library methods called |
|---|---|
| `jira_search_issues` | `jql()` |
| `jira_get_issue` | `issue()` + `get_issue_changelog()` + `get_issue_status_changelog()` + `issue_get_comments()` + `issue_get_worklog()` + `issue_get_watchers()` + `get_attachments_ids_from_issue()` + `get_issue_transitions()` |
| `jira_get_attachment` | `get_attachment()` |
| `jira_list_projects` | `projects()` |
| `jira_get_project` | `project()` + `get_project_components()` + `get_project_versions()` + `get_project_issues_count()` |
| `jira_search_users` | `user_find_by_user_string()` |
| `jira_get_myself` | `myself()` |
| `jira_list_boards` | `get_all_agile_boards()` |
| `jira_list_board_sprints` | `get_all_sprints_from_board()` |
| `jira_get_sprint_issues` | `get_all_issues_for_sprint_in_board()` |
| `jira_list_metadata` | `get_all_fields()` + `get_all_statuses()` + `get_all_priorities()` |

The bundled tools (`jira_get_issue`, `jira_get_project`, `jira_list_metadata`)
take no flags — they always return every facet. If a payload is larger than
needed for a specific question, that's fine; the cost of one big call is lower
than the cost of several serial small ones.

Anything in this document that's **not** mapped to a tool above is intentionally
excluded — either because it's a write operation, or because it's niche enough
that the AI client can always reach for `jira` directly in Python if needed.
