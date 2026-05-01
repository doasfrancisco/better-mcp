---
name: bring-context
description: Pull context from a previous entire-tracked session into the current chat. Lists sessions in the current repo (or any path passed as arg), lets the user pick when more than one matches, writes a 6-section compaction summary to entire_context_<id>.md in cwd, and feeds the same summary into chat. Use when the user says "bring context", "import context", "pull from session", or invokes /bring-context.
---

# Bring Context

Pull context from a previous `entire`-tracked session into this chat as both a persistent file and live agent context.

## STOP — Rules

1. **The picker is interactive.** When 2+ candidate sessions exist, list them, then STOP your turn and wait for the user to pick.
2. **Read transcripts only after the pick.** Listing reads only small JSON metadata; only the picked session's full transcript is parsed.
3. **Never auto-answer Unanswered Questions.** If the imported session ended on an open question, present it and halt.
4. **Do NOT invoke the `entire` CLI.** Read JSON files and transcripts directly. The skill works without `entire` on PATH.
5. **Never modify the source session's repo.** Only write to the current cwd.

## Inputs

- `/bring-context` — sessions in `<cwd>/.git/entire-sessions/`
- `/bring-context <repo-path>` — sessions in `<repo-path>/.git/entire-sessions/`
- `/bring-context <session.json>` — skip picker, use this exact session
- `/bring-context <hex-prefix>` — match unique prefix in cwd's session list

## Flow

### 1. Resolve source

- No arg → `source = <cwd>/.git/entire-sessions/`
- Arg is a `.json` file (path exists, ends in `.json`) → use directly, jump to step 4
- Arg is a directory → `source = <arg>/.git/entire-sessions/`
- Arg matches `^[a-f0-9]+$` (and is not a path) → search `<cwd>/.git/entire-sessions/` for a unique prefix match; if 1 match, use it; if 0 or 2+, halt with the matches printed
- If `source` doesn't exist → halt: `No entire sessions at <path>.`

### 2. Identify the active session (to exclude)

Glob `<cwd>/.git/entire-sessions/*.json`. The one with `phase == "active"` is the currently running session. Record its `session_id`. If none found, exclude nothing.

### 3. List candidates

Glob `<source>/*.json`. For each, parse and read only:
- `session_id`, `agent_type`, `model_name`, `last_prompt`, `last_interaction_time`, `files_touched`, `base_commit`, `transcript_path`

Filter out the active `session_id`. Sort by `last_interaction_time` DESC.

Branch on count:
- **0** → halt: `No importable sessions in <source>.`
- **1** → auto-pick, jump to step 4
- **2+** → print numbered list (format below), **STOP your turn**, wait for the user to reply with a number or session ID

```
Found <N> sessions in <source>
(excluding current session <short-id>)

  1. <3hex>  <agent_type>  <model_name>  <relative time>  "<last_prompt[:80]>"  (<N> files)
  2. <3hex>  ...
  ...

Which one? (1-N, or paste a session ID)
```

If 20+ sessions, show only the 20 most recent and add: `Showing 20 of <total> — pass a session ID to pick directly.`

### 4. Read transcript

From the picked session's JSON, get `transcript_path`. Extract the relevant lines:

```bash
grep -E '"type":"(message|function_call|user|assistant)"' "<transcript_path>" | cut -c1-2000
```

If the output exceeds ~500 lines, fall back to head + tail to capture original task and final state:

```bash
grep -E '"type":"(message|function_call|user|assistant)"' "<transcript_path>" | tail -100 | cut -c1-2000
grep -E '"type":"(message|function_call|user|assistant)"' "<transcript_path>" | head -20 | cut -c1-2000
```

If the transcript file is missing, halt: `Transcript missing at <path> — likely recorded on a different machine.`

Do NOT show the raw grep output to the user. Process it internally to compose the summary in step 6.

### 5. Stale-context check

The check must run against the **source repo**, not cwd. The source repo path comes from the session JSON's `worktree_path` field (when importing from a different repo, this points there; when importing from the current repo, it equals cwd).

```bash
git -C "<worktree_path>" rev-parse HEAD
```

Compare to `base_commit` from the picked session JSON. If they differ at all (even by one commit), record this for inclusion in the file and chat output.

If `worktree_path` is missing or unreadable (e.g. moved repo), skip the check rather than guessing.

### 6. Compose the summary

From the grep output (step 4) plus the session JSON metadata, produce 6 sections. Be concise but complete — err toward keeping detail that prevents duplicate work or repeated mistakes.

1. **Task Overview** — user's core request, success criteria, stated constraints
2. **Current State** — completed work, files modified, decisions made, artifacts produced
3. **Important Discoveries** — technical constraints, rationale, errors hit and resolutions, failed approaches and why
4. **Next Steps** — specific remaining actions, blockers, priority ordering
5. **Context to Preserve** — user preferences, domain details, commitments
6. **Unanswered Question** — only if the last user-assistant exchange ended on a question the user never answered. Capture exactly as asked.

### 7. Build the filename

`short_id` = first **3 hex chars** of `session_id`.

`filename` = `<cwd>/entire_context_<short_id>.md`.

If it exists, version-bump: try `entire_context_<short_id>_v2.md`, `_v3.md`, ... until a free name is found. Never overwrite.

### 8. Write the file

```markdown
> Imported from session `<full session_id>` (<agent_type> · <model_name>) — repo `<basename of worktree_path>` @ commit `<base_commit[:7]>` — <ISO timestamp>
> Source transcript: `<transcript_path>`

# Context from session <short_id>

[If stale: > ⚠️ HEAD has moved since this session (base `<base[:7]>`, current `<HEAD[:7]>`). File references may be out of date.]

## Task Overview
...

## Current State
...

## Important Discoveries
...

## Next Steps
...

## Context to Preserve
...

## Unanswered Question
(only if applicable)

---

*Files touched: <comma-separated, from session JSON's `files_touched` field>*
*Reconstruct: `entire explain --session <full session_id>`*
```

### 9. Print summary to chat

Output the same 6-section summary in chat (so the agent has it in live context) and end with: `Wrote <filename>.`

If stale, prefix with the same ⚠️ warning line.

### 10. Continue

- If summary contains an Unanswered Question → present it to the user and halt. The user is the decision-maker; do not pick a default.
- Otherwise → start the next step from the summary. Do not ask for permission.

## Notes

- 3-char short IDs collide easily (4096 possibilities). Version-bump guarantees the file is never overwritten; the full UUID in the header disambiguates between collisions.
- The skill's only side effect is writing one `.md` file in cwd. It never modifies git, never installs anything, never touches the source repo.
- If the grep recipe returns nothing (different agent's transcript shape), fall back to summarizing from the session JSON's `last_prompt` + `files_touched` only and note reduced fidelity in the file.
