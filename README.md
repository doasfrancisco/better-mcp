# MCP Servers & Skills

Personal collection of MCP servers and skills for Claude Code.

## MCP Servers

### Gmail

Full Gmail control with multi-account support, tag system, and bulk operations.

```bash
claude mcp add -s user gmail -- uv run --directory /path/to/mcps/gmail fastmcp run server.py
```

See [mcps/gmail/README.md](mcps/gmail/README.md) for setup (OAuth credentials, accounts config).

### Resend

Send emails via the Resend API. `--sender` and `--reply-to` are optional — if omitted, the tool asks the user each time.

```bash
claude mcp add -s user resend -- node /path/to/mcps/resend/build/index.js --key=RESEND_API_KEY --sender=you@domain.com --reply-to=reply@domain.com
```

See [mcps/resend/README.md](mcps/resend/README.md) for setup.

### Playwright

Browser automation — installed globally via npx, no local code.

```bash
claude mcp add -s user playwright -- npx @anthropic-ai/mcp-playwright@latest
```

## Skills

Skills are installed with `npx skills add`, pointing to a GitHub URL or local path.

### pulso-slides

Creates clean, minimal PowerPoint presentations from Markdown.

```bash
npx skills add https://github.com/doasfrancisco/mcp_servers/tree/master/skills/pulso-slides
```

See [skills/pulso-slides/SKILL.md](skills/pulso-slides/SKILL.md) for usage.

## Reference

- [THOUGHTS.md](THOUGHTS.md) — lessons learned building MCP servers
- [HOOKS.md](HOOKS.md) — Claude Code hooks patterns
- [LEGACY.md](LEGACY.md) — old build pipeline (removed)
