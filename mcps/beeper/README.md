# Beeper MCP Server

Query Beeper Desktop (local API at `http://localhost:23373`) from AI assistants.

## Tools

| Tool | What it does |
|------|---------------|
| `beeper_get_my_info` | Returns `/v1/info` server metadata + `/v1/accounts` connected networks. |

## Setup

1. Install [Beeper Desktop](https://www.beeper.com) v4.1.169+.
2. Enable the Desktop API: **Settings → Developers → Beeper Desktop API → toggle on**.
3. Create an access token: **Settings → Developers → Approved connections → "+"**.
4. Add it to the repo root `.env`:
   ```
   BEEPER_ACCESS_TOKEN='...'
   ```
5. Install dependencies:
   ```bash
   cd mcps/beeper
   uv sync
   ```

## Run it locally

```bash
uv run fastmcp run server.py
```

## Connect to Claude Code

```bash
claude mcp add -s user beeper -- uv run --directory C:/Francisco/github-repositories/mcp_servers/mcps/beeper fastmcp run server.py
```
