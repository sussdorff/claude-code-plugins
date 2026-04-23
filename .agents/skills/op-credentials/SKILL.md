---
name: op-credentials
model: haiku
description: Read, list, and create service credentials in 1Password. Use when needing API keys, service passwords, or creating credentials. Triggers on 1password, 1Password, op credentials, api key, service credentials, op read, op://, op item, vault, password speichern. Not for personal logins or SSH keys.
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

The 1Password **Service Account** (read-only on "API Keys" vault) is used for automated/non-interactive access. The token lives in `~/.claude/settings.json` under `env.OP_SERVICE_ACCOUNT_TOKEN`.

- **Claude Code sessions**: `OP_SERVICE_ACCOUNT_TOKEN` is auto-injected from settings.json. `op read` works without unlock.
- **Normal shell sessions**: Token is NOT in the environment. Use this pattern in `.zshrc`:
  ```bash
  # Extract SA token from Claude settings for non-interactive op read
  if [[ -z "$OP_SERVICE_ACCOUNT_TOKEN" ]]; then
    _op_sa_token="$(python3 -c 'import json; print(json.load(open("'$HOME'/.claude/settings.json"))["env"]["OP_SERVICE_ACCOUNT_TOKEN"])' 2>/dev/null)"
    [[ -n "$_op_sa_token" ]] && export MY_SECRET="$(OP_SERVICE_ACCOUNT_TOKEN=$_op_sa_token op read 'op://API Keys/Item/field' 2>/dev/null)"
    unset _op_sa_token
  else
    export MY_SECRET="$(op read 'op://API Keys/Item/field' 2>/dev/null)"
  fi
  ```
- **Service Account limitations**: Read-only. Cannot create or modify items. For writes, generate a script (see "Creating New Credentials" below).

## Reading Credentials

```bash
# Read a single field
op read "op://API Keys/<ServiceName>/<FieldName>"

# Examples
op read "op://API Keys/Prowlarr/API Key"
op read "op://API Keys/Komga/username"
op read "op://API Keys/Komga/password"
op read "op://API Keys/Audiobookshelf/API Key"
op read "op://API Keys/Dolt Root/password"
```

In Python code, use subprocess to call `op read`:
```python
import subprocess
def read_op_credential(service: str, field: str) -> str | None:
    try:
        result = subprocess.run(
            ["op", "read", f"op://API Keys/{service}/{field}"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
```

## Listing Credentials

```bash
op item list --vault "API Keys"
```

## Creating New Credentials

**CRITICAL: Never create 1Password items directly.** Always generate a `/tmp/op-create-<service>.sh` script for the user to execute manually.

### For API Key services:

```bash
#!/bin/bash
op item create \
  --vault "API Keys" \
  --category "API Credential" \
  --title "<ServiceName>" \
  --url "<service-url>" \
  "API Key[password]=<the-api-key>"
```

### For Basic Auth services:

```bash
#!/bin/bash
op item create \
  --vault "API Keys" \
  --category "Login" \
  --title "<ServiceName>" \
  --url "<service-url>" \
  --generate-password='20,letters,digits' \
  "username=<username>"
```

### For Database services:

```bash
#!/bin/bash
op item create \
  --vault "API Keys" \
  --category "Database" \
  --title "<ServiceName>" \
  --tags "<tag1>,<tag2>" \
  "username=<user>" \
  "password=<password>" \
  "hostname=<host>" \
  "port=<port>" \
  "database=<dbname>" \
  "notesPlain=<description>"
```

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
