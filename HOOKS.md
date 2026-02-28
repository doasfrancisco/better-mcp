# Hooks

Claude Code hooks run shell commands in response to lifecycle events.

## Scopes

| Scope | Config location | Lifetime |
|-------|----------------|----------|
| Global | `~/.claude/settings.json` | Always active |
| Project | `.claude/settings.local.json` | Active in this repo |
| Skill | `SKILL.md` frontmatter | Active while skill runs |

## Events

| Event | When |
|-------|------|
| `SessionStart` | When a conversation begins |
| `UserPromptSubmit` | When the user sends a message |
| `PreToolUse` | Before a tool is called |
| `PostToolUse` | After a tool completes |
| `Notification` | When Claude sends a notification (e.g. background task done) |
| `Stop` | When the agent finishes |

## Matcher

Use `matcher` on `PreToolUse` / `PostToolUse` to filter by tool name. Supports regex: `"Bash"`, `"Edit|Write"`, `"*"` for all.

## Current setup: sound effects

Hooks call a Python script (`~/.claude/play-sound.py`) that plays `.wav` files. The script takes a label and a file path as arguments.

**How sound resolution works:** Global hooks in `~/.claude/settings.json` define the default sounds. A project can override them by defining the same events in `.claude/settings.local.json` with different sound files. When local hooks are defined for an event, they replace the global hooks for that event.

### Sound events

| Event | Label | Example file |
|-------|-------|-------------|
| `SessionStart` | `start.wav` | `start.wav` |
| `UserPromptSubmit` | `submit.wav` | `submit.wav` |
| `Notification` | `notify.wav` | `notify.wav` |
| `Stop` | `done.wav` | `done.wav` |

Global hooks point to a default sound pack. Per-project overrides point to a different folder (e.g. `sounds/start.wav`) to give each project its own character.

## Skill hooks

Skills can define hooks in their `SKILL.md` frontmatter. These only run while the skill is active and clean up automatically.

```yaml
---
hooks:
  Stop:
    - hooks:
        - type: command
          command: "echo %DATE% %TIME% - skill completed >> %USERPROFILE%\\.claude\\skill-usage.txt"
---
```

Skill hooks support a `once: true` option to run only on the first match.

## Windows syntax

| Unix | Windows |
|------|---------|
| Single quotes `'...'` | Double quotes (escaped in JSON) |
| `~` | `%USERPROFILE%` |
| `\(...)` interpolation in jq | `[...] \| join()` to avoid nested quotes |

`jq` is required for hooks that parse tool input: `winget install jqlang.jq`
