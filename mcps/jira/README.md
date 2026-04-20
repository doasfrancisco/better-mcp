# jira — MCP server for Jira Cloud

Uses [atlassian-python-api](https://github.com/atlassian-api/atlassian-python-api) with email + API token auth (`cloud=True`).

## Credentials

In repo root `.env`:

```
JIRA_URL=<domain>
JIRA_EMAIL=<account email>
JIRA_API_TOKEN=<atlassian API token>
```