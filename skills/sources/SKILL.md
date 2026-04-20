---
name: sources
description: Set up nia.md at the current project root. Analyzes dependency manifests, filters to the libraries worth binding, resolves them against Nia, and writes nia.md using a fixed template. Then asks if the user wants to add docs or other repos. Use when the user says "set up sources", "create nia.md", "bind nia to this project", or invokes /sources.
---

# sources

Generate `nia.md` at the project root so future Claude sessions know which Nia-indexed sources map to this project's dependencies.

## 1. Check for an existing nia.md

Look for `nia.md` (case-insensitive) at the project root. If it exists, read it and tell the user it's already set up. Ask if they want to **refresh** it (regenerate from current dependencies). If they say no, stop.

## 2. Find dependency manifests

Scan the project root up to depth 4, **excluding** `node_modules/`, `.venv/`, `venv/`, `__pycache__/`, `dist/`, `build/`:

- `pyproject.toml` — read `[project].dependencies` (NOT `[tool.*]` dev groups)
- `requirements.txt` — one dep per line
- `package.json` — read `dependencies` only, NOT `devDependencies`
- `Cargo.toml` — `[dependencies]`
- `go.mod` — `require` block

In monorepos, collect the **union** of runtime deps across every manifest. Strip version specifiers and extras — you only need names.

## 3. Filter to the deps worth binding

Not every dep deserves a Nia source. The goal is a short list of libraries that define the project's problem domain — the ones you'd look up API docs for in a typical session.

**Skip these categories:**

- **Config/env**: `python-dotenv`, `dotenv`, `configparser`, `pyyaml`, `toml`
- **Basic HTTP primitives**: `requests`, `urllib3`, `httpx`, `aiohttp`, `axios`, `node-fetch`, `got`
- **Tiny utilities**: `pillow`, `pystray`, `cors`, `body-parser`, `zod`, `pydantic`, `joi`, `ajv`
- **Dev tooling**: `pytest`, `jest`, `eslint`, `prettier`, `typescript`, `tsx`, `nodemon`, `vitest`
- **Generic helpers**: `lodash`, `moment`, `dayjs`, `uuid`, `chalk`, `ms`

**Keep** frameworks, SDKs, platform libraries, and anything domain-specific. Example from this repo: keep `fastmcp`, `google-api-python-client`, `spotipy`, `beeper-desktop-api`, `@modelcontextprotocol/sdk`, `whatsapp-web.js`, `electron`, `express`, `glpi`. Skip `python-dotenv`, `httpx`, `pillow`, `pystray`, `cors`, `zod`, `urllib3`.

When in doubt, **keep** it — the user can drop rows before the file is written.

Show the user the proposed keep list and the skip list, and wait for them to approve or edit before continuing.

## 4. Resolve each dep against Nia

For every kept dep, run:

```bash
nia sources resolve "<name>"
```

The resolver accepts package names, URLs, or `owner/repo` identifiers. From each result capture the canonical `identifier`. **Strip any branch suffix** (`:main`, `:master`, `:trunk`) — use the bare `owner/repo` form.

If a dep returns `Source resource not found`, skip it and remember the name. You'll list unresolved deps at the end so the user can decide whether to `nia repos index <owner/repo>`.

## 5. Write nia.md

Use this **exact template** at the project root. Replace only the `<project-name>` token and the rows of the Sources table. **Do not change the Rules section. Do not change the Examples section's docs lines (the `nia sources resolve "https://platform.claude.com/docs"` block and the `--docs` arg in the multi-source query).**

````markdown
# Nia sources for <project-name>

## Rules

- **Never pipe `nia` output through `head -N` or `tail -N`.** The output can be 2000+ lines. You MUST read ALL of it. If the output is split across chunks, read every chunk before proceeding. Missing a single source leads to wrong follow-up searches and wasted user time.
- **If the source is a package/library, always ask how to install it** (pip name, Python/Node version, any extras). E.g. `"how do I install X - pip name, python version, async extras?"`

## Sources

| Dep | Nia identifier | Type |
|---|---|---|
| `<dep>` | `<owner/repo>` | repository |

## Examples

```bash
nia search query "<topic tied to one of this project's repos>" --repos <owner/repo>
nia search query "<another topic>" --repos <another-repo>
nia repos tree <one-of-the-repos>
nia repos read <one-of-the-repos> <plausible-file-path>
nia repos grep <one-of-the-repos> "<plausible-symbol>"

nia sources resolve "https://platform.claude.com/docs" --type documentation
nia sources tree <UUID>
nia sources read <UUID> build-with-claude/prompt-caching.md
nia sources grep <UUID> "cache_control"
```

### Multi-source query

```bash
# Example
nia search query "<cross-cutting topic>" \
  --repos <repo-a>,<repo-b> \
  --docs "https://platform.claude.com/docs"
```
````

For the five code-example lines at the top of the bash block, pick queries that realistically exercise this project's repos — same *shape* as the examples above, just different sources. Don't invent file paths; use ones you've actually seen, or keep the command at the tree/grep level where no path is needed.

## 6. Ask about extras

Once nia.md is written, ask the user:

> Do you want to add any other sources? For example docs sites (e.g. `https://docs.stripe.com`), or other repos you reference often but aren't in the dep manifest.

For each extra:

- **Docs URL**: `nia sources resolve "<url>" --type documentation`. If it resolves, append it to the Sources table with Type `documentation`. If not, suggest `nia sources index <url>`.
- **Repo**: `nia sources resolve "<owner/repo>"`. If not indexed, suggest `nia repos index <owner/repo>`.

Append each resolved extra to the Sources table with its correct `Type`.

## Commands to list and filter Nia sources

Use these verbatim — never pipe through `head` or `tail`. Read the whole output.

```bash
# Full list — use --all to paginate through every source
nia sources list --all
nia repos list --all
nia sources list --type repository --all
nia sources list --type documentation --all

# Resolve a name / URL / owner-repo to a Nia source (returns id, type, identifier)
nia sources resolve "<name>"
nia sources resolve "<owner/repo>"
nia sources resolve "<url>" --type documentation

# Index a new source
nia repos index <owner/repo>
nia sources index <root-doc-url>
```

## Rules

- NEVER include `devDependencies` — runtime deps only.
- NEVER include every dep — filter with step 3 first, then confirm with the user before resolving.
- NEVER modify the Rules section of nia.md or the example lines.
- NEVER pipe `nia sources list` / `nia repos list` through `head` or `tail`. Read the whole output.
- NEVER commit nia.md without showing the user the final contents.
- If a dep doesn't resolve, list it at the end as "Unresolved — may need `nia repos index <owner/repo>`" so the user can decide.
- Strip `:main` / `:master` / `:trunk` branch suffixes from identifiers before writing.
