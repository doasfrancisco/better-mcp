## Insights

See [THOUGHTS.md](THOUGHTS.md) for lessons learned building MCP servers (FastMCP quirks, Gmail API patterns, tool design).

## Hooks

See [HOOKS.md](HOOKS.md) for Claude Code hooks patterns (sound effects, skill hooks, Windows syntax).

## Old architecture

See [LEGACY.md](LEGACY.md) for the removed build pipeline (build-mcps, generate-mcp-config, config templates).

## After finishing a task

Update [FUTURE.md](FUTURE.md) — remove completed items and add any new ideas or next steps that came up during the work.

## Commits

Use conventional commits. No co-authoring. ALWAYS stage with `git add .` — before committing, check `.gitignore` to verify no file that should not be added is missing from it.

Every message MUST answer both **what** changed and **why** it changed. A message that only describes the what is wrong.

- `feat:` for new functionality
- `fix:` for bug fixes
- `chore:` for everything else

Bad: `feat: add repo mapping` — missing the why.
Good: `feat: add repo mapping to centralize project navigation`

Bad: `fix: update query logic` — what query? why?
Good: `fix: deduplicate subsidiary query to avoid double-counting schedules`

Bad: `chore: update dependencies` — why now?
Good: `chore: bump django to 4.2.9 to patch CVE-2024-XXXXX`
