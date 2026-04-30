---
name: op-credentials
model: haiku
description: Read, list, and create service credentials in 1Password. Use when needing API keys, service passwords, or creating credentials. Triggers on 1password, 1Password, op credentials, api key, service credentials, op read, op://, op item, vault, password speichern. Not for personal logins or SSH keys.
requires_standards: [english-only]
---

# op-credentials

Manage service credentials stored in the 1Password vault "API Keys". Read existing keys, list available services, and generate scripts for creating new entries.

## When to Use

- Need an API key or service password for a project config
- Checking which services already have credentials stored
- Setting up credentials for a new service (Prowlarr, SABnzbd, Komga, etc.)

## Architecture

All service credentials live in **1Password vault "API Keys"**. Three credential patterns exist:

| Pattern | Fields | Examples |
|---------|--------|----------|
| API Key | `API Key` | Prowlarr, SABnzbd, Audiobookshelf, Hetzner Cloud |
| Basic Auth | `username`, `password` | Komga, Calibre-web, Paperless-ngx |
| Token + Host | `API Key`, `Host-Name` | Audiobookshelf (has both) |
| Database | `username`, `password`, `hostname`, `port`, `database` | Dolt Root, Dolt Cloud, Dolt Local |

## Service Account vs Personal Account

The 1Password **Service Account** (read-only on "API Keys" vault) is used for automated/non-interactive access. The token lives in the active harness settings under `env.OP_SERVICE_ACCOUNT_TOKEN`.

- **Claude Code sessions**: `OP_SERVICE_ACCOUNT_TOKEN` is auto-injected from settings.json. `op read` works without unlock.
- **Normal shell sessions**: Token is NOT in the environment. See [`scripts/zshrc-op-snippet.sh`](scripts/zshrc-op-snippet.sh) for the `.zshrc` pattern that extracts the token from Claude settings for non-interactive `op read`.
- **Service Account limitations**: Read-only. Cannot create or modify items. For writes, generate a script (see "Creating New Credentials" below).

## Reading Credentials

See [`scripts/read-credentials.sh`](scripts/read-credentials.sh) for shell examples (single field read and common service examples).

In Python code, use subprocess to call `op read` — see [`scripts/read-credential.py`](scripts/read-credential.py) for the `read_op_credential(service, field)` helper function.

## Listing Credentials

```bash
op item list --vault "API Keys"
```

## Creating New Credentials

**CRITICAL: Never create 1Password items directly.** Always generate a `/tmp/op-create-<service>.sh` script for the user to execute manually.

### For API Key services:

See [`scripts/op-create-apikey.sh`](scripts/op-create-apikey.sh) for the template (vault "API Keys", category "API Credential", API Key field).

### For Basic Auth services:

See [`scripts/op-create-basicauth.sh`](scripts/op-create-basicauth.sh) for the template (category "Login", --generate-password, username field).

### For Database services:

See [`scripts/op-create-database.sh`](scripts/op-create-database.sh) for the template (category "Database", username/password/hostname/port/database/notesPlain fields).

### Workflow

1. Determine credential type (API Key vs Basic Auth vs Database)
2. Gather the values (from service config files, APIs, or user input)
3. Write script to `/tmp/op-create-<service>.sh`
4. Make executable: `chmod +x /tmp/op-create-<service>.sh`
5. Tell user to run the script: `eval $(op signin) && bash /tmp/op-create-<service>.sh`
6. Verify with `op item list --vault "API Keys" | grep <ServiceName>`

## Do NOT

- Create 1Password items directly via `op item create` in the session. WHY: User needs to authenticate with their own biometrics/password for write operations
- Store API keys in plain text config files as primary storage. WHY: 1Password is the source of truth, configs should reference `op read`
- Read credentials just to display them to the user. WHY: Unnecessary exposure; only read when needed for code/config
- Guess field names -- use `op item get "<ServiceName>" --vault "API Keys" --format json | jq '[.fields[] | .label]'` to discover fields
