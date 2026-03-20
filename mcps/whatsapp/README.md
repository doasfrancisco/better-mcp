# WhatsApp AI

Electron app wrapping WhatsApp Web with a built-in MCP server. Replaces the old Puppeteer-based WhatsApp MCP.

Opening the app = MCP server is live on port 39571. No hooks, no separate processes.

## Setup

```bash
cd mcps/whatsapp
npm install
npm run dist
```

First run: scan the QR code with your phone (WhatsApp Settings → Linked Devices). Session persists across restarts.

## Launching

### Option 1: Built .exe (recommended)

Run `dist/win-unpacked/WhatsApp AI.exe`. Pin to taskbar or create a desktop shortcut.

### Option 2: Terminal

```bash
cd mcps/whatsapp && npm start
```

### Rebuilding after code changes

```bash
npm run dist
```

## MCP config

Claude Code connects to `http://localhost:39571/mcp`:

```json
{
  "mcpServers": {
    "whatsapp": {
      "type": "http",
      "url": "http://localhost:39571/mcp"
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `whatsapp_sync` | Sync contacts/chats/messages from WhatsApp into local cache |
| `whatsapp_find` | Search contacts and chats by name, tag, date, or filter |
| `whatsapp_get_messages` | Read cached messages (no API calls) |
| `whatsapp_tag_contacts` | Add/remove tags on contacts |
| `whatsapp_send` | Send a text message (safe — uses official WhatsApp Web) |
