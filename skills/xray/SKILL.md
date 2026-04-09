---
name: xray
description: X-ray a codebase before reading it. Runs 5 git diagnostics — churn hotspots, bus factor, bug clusters, commit velocity, and revert frequency — then delivers a brief risk report. Use when the user says "xray", "scan this repo", or invokes /xray.
---

# xray

Run all 5 diagnostics, then deliver a single concise report. No preamble, no explaining what you're about to do — just run the commands and present findings.

## Commands

Run all 5 in parallel:

### 1. Churn hotspots — most-changed files in the last year

```bash
git log --format=format: --name-only --since="1 year ago" | sort | uniq -c | sort -nr | head -20
```

### 2. Bus factor — who built this

```bash
git shortlog -sn --no-merges
```

### 3. Bug clusters — files that keep breaking

```bash
git log -i -E --grep="fix|bug|broken" --name-only --format='' | sort | uniq -c | sort -nr | head -20
```

### 4. Commit velocity — momentum by month

```bash
git log --format='%ad' --date=format:'%Y-%m' | sort | uniq -c
```

### 5. Revert/hotfix frequency — firefighting signals

```bash
git log --oneline --since="1 year ago" | grep -iE 'revert|hotfix|emergency|rollback'
```

## Report format

After running the commands, deliver a short report with these sections:

**Hottest files** — top 5 highest-churn files. Flag any that also appear in the bug cluster list (these are the highest-risk files).

**Bus factor** — how concentrated is ownership? Call out if one person is 60%+ of commits. Note if top contributors appear inactive.

**Bug magnets** — files that keep breaking. Cross-reference with churn — files on both lists are the biggest risk.

**Velocity** — is the project accelerating, decelerating, or steady? Any gaps that suggest people leaving or momentum dying?

**Stability** — how many reverts/hotfixes in the last year? A few is normal. Every couple weeks means deploy trust is low.

End with a one-line verdict: is this codebase healthy, manageable, or on fire?
