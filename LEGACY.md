# Legacy Build Pipeline

Removed during repo pruning. Documented here for reference.

## What it was

A three-step pipeline to install, configure, and register MCP servers:

### 1. `scripts/build-mcps.js`

Iterated over `servers/` subdirectories, ran `npm install` + `npm run build` for each. Had special handling for nia (pipx) and supermemory (OAuth flow). Some servers were skipped via a hardcoded list.

### 2. `scripts/generate-mcp-config.js`

Read a `.env` file for API keys, then processed `config/<client>/mcp-servers.json` template files. Replaced `{{VARIABLE}}` placeholders with env values and wrote individual `generated-<server>.json` files per server per client (claude-code, claude-desktop, cursor).

### 3. `scripts/add-mcps-to-claude-code.js`

Interactive CLI that listed generated configs, showed which servers were already installed, and let you pick one to register via `claude mcp add-json`.

## Config structure

```
config/
├── claude-code/
│   ├── mcp-servers.json          (template with {{PLACEHOLDERS}})
│   └── generated-<server>.json   (output with real keys)
├── claude-desktop/
│   └── ...
└── cursor/
    └── ...
```

## .env / dotenv-vault

API keys lived in `mcps/.env`, with `.env.vault` and `.env.me` for the dotenv-vault service (`bunx dotenv-vault pull` to sync keys across machines).

## Why it was removed

The pipeline added complexity without value. `claude mcp add` with env vars is simpler and doesn't risk committing secrets via generated config files. Each server now documents its own setup command in its README.
