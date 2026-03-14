# Gmail MCP vs Google Workspace CLI — Comparison

Comparison of our Gmail MCP (`mcps/gmail/`) with Google's official Workspace CLI (`googleworkspace/cli`).

## Architecture

| | Our Gmail MCP | Google Workspace CLI |
|---|---|---|
| **Language** | Python (FastMCP) | Rust (clap CLI) |
| **Interface** | MCP tools (used by AI agents) | Shell commands (used by humans + AI agents) |
| **API access** | Hardcoded Gmail API calls via `google-api-python-client` | Dynamic — parses Google Discovery Documents at runtime for ALL Workspace APIs |
| **Auth** | OAuth2 per-account tokens, auto-refresh, web-based onboarding | OAuth2 via `gws auth login`, supports multiple Google services |
| **Multi-account** | Yes — aliases (personal/work/university), default account, cross-account operations | No — single authenticated user per session |
| **Agent integration** | Native MCP protocol — tools callable by Claude, Cursor, etc. | Skills (SKILL.md files) that AI agents read as instructions for shell commands |

## Gmail Feature Comparison

### What both have

| Feature | Our MCP | GWS CLI |
|---|---|---|
| **Search/list emails** | `gmail_search_messages` with date shorthands, multi-account | `gws gmail users messages list` with Gmail query syntax |
| **Read email** | `gmail_read_message`, `gmail_read_thread` | `gws gmail users messages get` |
| **Send email** | `gmail_send_message` (to, cc, bcc, HTML) | `gws gmail +send` (to, cc, bcc, HTML, dry-run) |
| **Reply** | `gmail_send_message` with `reply_to_message_id` (auto-threads) | `gws gmail +reply` (dedicated, auto In-Reply-To/References/threadId) |
| **Drafts** | `gmail_create_draft`, `gmail_list_drafts` | Raw API: `gws gmail users drafts create/list` |
| **Trash** | `gmail_trash_messages` (batch), `gmail_untrash_message` | Raw API: `gws gmail users messages trash/untrash` |
| **Labels/tags** | `gmail_tag_messages`, `gmail_list_tags`, `gmail_delete_tag` | Raw API: `gws gmail users labels list/create`, `messages modify` |
| **Threading** | Auto-threads replies via Message-ID headers | Auto-threads via In-Reply-To + References headers |

### What GWS CLI has that we don't

| Feature | GWS CLI approach | Value for us |
|---|---|---|
| **Forward** | `gws gmail +forward` — dedicated command with proper `Fwd:` subject, forwarded-message quoting block (plain + HTML), threading headers | **High** — we have no forwarding. User must manually copy-paste email content into a new send. |
| **Reply-all** | `gws gmail +reply-all` — auto-resolves all To/CC recipients, deduplicates, has `--remove` to exclude specific addresses | **Medium** — our `send_message` can reply but doesn't auto-resolve all original recipients. The AI has to extract them manually from the read result. |
| **Watch/push notifications** | `gws gmail +watch` — real-time email streaming via Pub/Sub, NDJSON output, configurable polling, output to files | **Low** — requires GCP project + Pub/Sub setup. Our use case is interactive (user asks AI to check email), not streaming. |
| **Triage view** | `gws gmail +triage` — read-only unread inbox summary (sender, subject, date) | **Low** — our `gmail_search_messages` already does this with `query="is:unread"`. |
| **Dry-run mode** | `--dry-run` flag on send/reply/forward — shows what would be sent without sending | **Medium** — useful for AI safety. Currently we rely on MCP instructions ("tell user before sending") but dry-run is a harder guarantee. |
| **Gmail filters** | Recipe: create/list/manage inbox filters | **Low** — niche. Filters are a "set and forget" feature users configure once in Gmail settings. |
| **Vacation responder** | Recipe: enable/disable auto-reply with date ranges | **Low** — niche, very infrequent use. |
| **Save attachments** | Recipe: download attachments from emails | **Medium** — we currently show attachment metadata but can't download them. |
| **Full raw API access** | Any Gmail API endpoint via Discovery Documents (`gws gmail users messages <method>`) | **N/A** — different architecture. MCP tools are curated, not a generic API proxy. |
| **Schema introspection** | `gws schema gmail.users.messages.send` — inspect API schemas | **N/A** — not applicable to MCP tools. |

### What we have that GWS CLI doesn't

| Feature | Our approach | Why it matters |
|---|---|---|
| **Multi-account** | Search/read/tag across personal + work + university in one call | GWS CLI operates on one Google account at a time. Multi-account is our killer feature for a user managing several inboxes. |
| **Auto-sort (AI tagging)** | `auto/*` labels, `skip_auto` filter, auto-skipped counts | AI-powered email categorization with smart defaults. GWS CLI has no concept of AI-sorted mail. |
| **Unsubscribe** | `gmail_unsubscribe` — RFC 8058 one-click HTTP unsubscribe with URL fallback | GWS CLI has no unsubscribe feature at all. |
| **Batch operations** | `gmail_tag_messages` processes mixed tag operations in one call; `gmail_trash_messages` batches across accounts | GWS CLI operates message-by-message via raw API. |
| **Tag system abstraction** | Human-friendly tags (`important`, `credentials`, `contacts`, custom) mapped to Gmail labels | GWS CLI works with raw label IDs. |
| **Auto-mark-as-read** | Search results automatically marked as read | GWS triage is explicitly read-only. |
| **Zero-config onboarding** | Web UI opens on first run, guides through OAuth + account setup | GWS CLI requires `gws auth login` + familiarity with CLI. |
| **Native MCP protocol** | Tools directly callable by any MCP-compatible AI agent | GWS CLI requires the AI to shell out and parse stdout. |

## Verdict

### Worth adopting from GWS CLI

1. **Forward** (high value) — We should add `gmail_forward_message`. Their implementation is solid: proper `Fwd:` subject handling, quoted forwarded-message block with From/Date/Subject/To headers, HTML support, threading headers. This is a real gap — users can't forward emails through our MCP today.

2. **Reply-all recipient resolution** (medium value) — Our `send_message` handles replies but the AI has to manually figure out who to CC. A dedicated reply-all mode that auto-resolves original To/CC recipients (with deduplication and self-exclusion) would make group email conversations smoother.

3. **Attachment download** (medium value) — We show attachment metadata but can't retrieve the actual files. Adding `gmail_get_attachment` that downloads to a local path would unlock "save this PDF" workflows.

### Not worth adopting

- **Watch/push notifications** — Requires GCP infrastructure. Our interactive model (user asks, AI checks) works well for our use case.
- **Triage view** — Already covered by `gmail_search_messages`.
- **Gmail filters/vacation responder** — Too niche for a curated MCP tool set.
- **Dry-run mode** — Nice-to-have but our MCP instructions already enforce "confirm before sending" at the AI behavior level, which is effectively the same thing.
- **Full raw API proxy** — Fundamentally different architecture. Our curated tools are better for AI agents than a generic API surface.
- **Schema introspection** — Not applicable.

### Our advantages to keep

- **Multi-account** is the single biggest differentiator. GWS CLI can't do this.
- **Auto-sort system** with `auto/*` labels is a genuinely novel AI-email pattern.
- **Batch operations** with per-item params are more efficient than GWS CLI's one-at-a-time approach.
- **Unsubscribe** fills a gap that even Google's own CLI doesn't cover.

## Next steps

Add to FUTURE.md:
- `gmail_forward_message` — forward an email to new recipients with proper quoting
- `gmail_get_attachment` — download email attachments to local filesystem
- Consider reply-all recipient auto-resolution in `gmail_send_message`
