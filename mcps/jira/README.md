# Jira MCP Server

Read-only access to a Jira Cloud instance via FastMCP. Uses [atlassian-python-api](https://github.com/atlassian-api/atlassian-python-api) with email + API token auth (`cloud=True`).

## Setup

1. **Jira API token** — Create one at https://id.atlassian.com/manage-profile/security/api-tokens (Atlassian account → Security → API tokens)
2. **Environment** — Add to the repo root `.env`:
   ```
   JIRA_URL='https://your-domain.atlassian.net'
   JIRA_EMAIL='your_account@email.com'
   JIRA_API_TOKEN='your_api_token'
   ```
3. **Install** — `uv sync` inside `mcps/jira/`
4. **Add to Claude Code:**
   ```bash
   claude mcp add -s user jira -- uv run --directory /path/to/jira fastmcp run server.py
   ```