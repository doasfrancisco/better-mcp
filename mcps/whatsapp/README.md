# WhatsApp MCP Server

MCP server for reading WhatsApp messages and contacts via `whatsapp-web.js`.

## Setup

```bash
cd mcps/whatsapp
npm install
```

## First run — QR authentication

```bash
node server.js
```

A Chromium window opens with a QR code. Scan it with WhatsApp on your phone (Settings → Linked Devices → Link a Device). After scanning, the session is saved to `.wwebjs_auth/` and subsequent runs reconnect headlessly.

## Register with Claude Code

```bash
claude mcp add -s user whatsapp -- node C:/Francisco/github-repositories/mcp_servers/mcps/whatsapp/server.js
```

Then restart Claude Code.

## Tools

| Tool | Description |
|------|-------------|
| `whatsapp_sync` | Sync data from the API. No params syncs contacts+chats. `what: "messages"` syncs messages for specific chats. |
| `whatsapp_find` | Find people or groups by name, tag, date, or filter. Cache-only. |
| `whatsapp_get_messages` | Get cached messages from a chat. Cache-only. |
| `whatsapp_tag_contacts` | Add or remove tags from contacts/groups. |

Write tools (send, reply, react, delete) are defined but commented out in `server.js` — uncomment when ready.

## Re-authentication

If the session expires, delete `.wwebjs_auth/` and run `node server.js` again to re-scan the QR.
