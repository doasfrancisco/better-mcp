# WhatsApp MCP Server (Beeper-backed)

Query WhatsApp (and other networks) via the Beeper Desktop local API at `http://localhost:23373`. Supersedes the Electron/Puppeteer implementations in `mcps/whatsapp_legacy/` and `mcps/whatsapp_legacy_v2/`.

## Tools

| Tool | What it does |
|------|---------------|
| `beeper_get_my_info` | Returns `/v1/info` server metadata + `/v1/accounts` connected networks. |
| `whatsapp_list_chats` | List WhatsApp chats (DMs + groups) filtered by `query`, `tag`, and/or `since` (ISO timestamp). |
| `whatsapp_get_messages` | Read messages in a chat by `chat_id`. Default window: last 48h; override via `since` (ISO datetime). |
| `whatsapp_download_files` | Download attachment tokens from `get_messages` output into `~/Downloads`. |
| `whatsapp_tag_contacts` | Add/remove tags on chats by `chat_id` (from `list_chats`). Batch: `[{chat_id, tags, action}]`. |

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
   cd mcps/whatsapp
   uv sync
   ```

## Run it locally

```bash
uv run fastmcp run server.py
```

## Connect to Claude Code

```bash
claude mcp add -s user whatsapp -- uv run --directory C:/Francisco/github-repositories/mcp_servers/mcps/whatsapp fastmcp run server.py
```
