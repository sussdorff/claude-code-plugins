---
name: dolt
description: >
  Troubleshoot beads Dolt failures: `bd dolt` push/pull errors, merge conflicts,
  embedded/shared-server mode problems, remote auth issues, local DB recovery, re-clone,
  reflog restore, and broken .beads Dolt config. Use whenever beads sync or Dolt
  infrastructure is failing, including symptoms like "beads do not sync", "cannot push
  issues", "no common ancestor", "not supported in embedded mode", or "lost local
  database". Read the beads changelog first. Do not use for normal beads tracking (`bd
  create/ready/close`), standalone Dolt databases, or regular git push/pull.
---

# dolt

> **Version gate**: The SessionStart hook (`beads-version-gate.sh`) ensures the local `bd`
> version matches the latest GitHub release. If this skill's instructions conflict with
> actual `bd` behavior, trust `bd --help` and the CHANGELOG over this document.

## First Step: Read the Changelog

Before diagnosing any issue, **always** check which beads version is installed and read the
relevant changelog sections. Breaking changes between versions are the #1 cause of "it was
working before" problems.

```bash
bd --version
# Then read the changelog for recent breaking changes:
cat /opt/homebrew/Cellar/beads/$(bd --version | awk '{print $3}')/CHANGELOG.md | head -120
```

Scan for keywords related to the current problem (embedded, server, shared, push, pull, etc.).
Version upgrades frequently change mode detection logic, metadata.json schema, and default
behaviors. Understanding what changed prevents wasted time on outdated fix procedures.

## Golden Rules

**NEVER call `/opt/homebrew/bin/dolt` directly** for push/pull/commit. Always use `bd dolt`
subcommands. The `bd` wrapper handles credentials, database selection, and server connection.

**Exception**: `dolt` CLI is acceptable for low-level SQL and cloning that `bd dolt` doesn't expose:
- `dolt --host ... --port ... --no-tls sql -q "..."` — direct SQL against local server
- `dolt clone` — initial database setup (see [Re-Clone Local Database](#re-clone-local-database))

**ALWAYS push with: `bd dolt pull && bd dolt push --force`.** Dolt has a known bug
(dolthub/dolt#10807) where every push dirties the remote's working set, causing the next
push to fail with "target has uncommitted changes". The `--force` here is safe — it overwrites
phantom dirty state, NOT commit history. Pulling first ensures other users' commits are merged.
Do NOT try to fix the dirty working set (DOLT_CHECKOUT, DOLT_RESET, server restart — none work).
**Exception**: For "no common ancestor" errors, do NOT force-push — re-clone locally instead.

**NEVER use `pkill` to stop the Dolt server.** Hard-killing the process corrupts journal files.
Always use `bd dolt stop`. If `bd dolt stop` fails, investigate why — do not escalate to `pkill`.

## Quick Triage

```bash
bd --version                                    # Version check
cat .beads/metadata.json                        # Check dolt_mode (embedded or server)
cat .beads/config.yaml | grep shared            # shared-server: true or false
bd dolt show                                    # Server mode only (fails in embedded)
bd stats                                        # Works in both modes — verifies DB access
```

| Symptom | Go to |
|---------|-------|
| Migrate embedded → shared-server | [Migrate Embedded to Shared-Server](#migrate-embedded-to-shared-server) |
| Embedded mode push fails repeatedly | [Embedded Mode — Known Broken](#embedded-mode--known-broken) |
| `not supported in embedded mode` | [Embedded Mode Fallback](#embedded-mode-fallback-since-0633) |
| `bd dolt push/pull` fails | [Diagnose Push Failures](#diagnose-push-failures) |
| No `.beads/` at all | [New Project Setup](#new-project-setup) |
| Stale files, wrong port | [Fix Misconfigured Project](#fix-existing-misconfigured-project) |
| Local DB missing/corrupted | [Re-Clone Local Database](#re-clone-local-database) |
| `corrupted journal` / `invalid journal record length` | [Journal Corruption Recovery](#journal-corruption-recovery) |
| Remote data lost | [Remote Recovery via Reflog](#remote-recovery-via-reflog) |
| Remote DB doesn't exist | [Create Remote DB](#create-remote-db) |
| `schema_migrations` dirty state on remote | [Known Issues](#known-issues) — drop table locally, force-push once |
| Fleet-wide fix | Run `scripts/migrate-fleet-shared-server.sh` or read `references/fleet-cleanup.md` |
| New team member | Read `references/team-onboarding.md` |

## Architecture

**Recommended mode: shared Dolt server** (`bd init --shared-server`). One `dolt sql-server`
process serves ALL projects from `~/.beads/shared-server/dolt/`. Push/pull uses the SQL
protocol which does not dirty the remote working set. `bd` manages the server lifecycle
automatically.

**Auto-start (v1.0.0+)**: `bd` transparently starts the shared server on first use — do
NOT add defensive `bd dolt start` calls to every workflow. Only run `bd dolt start`
explicitly when recovering from `bd dolt stop` or when diagnosing a "server connection
failed" error. There is no LaunchAgent or launchd keep-alive — the server runs as a
child of the first `bd` invocation and persists until machine reboot or `bd dolt stop`.

**Embedded Dolt** (`bd init`, the default since v1.0.0) is **NOT WORKING RELIABLY** for
push/pull when the remote runs a Dolt SQL server (our setup). See
[Embedded Mode — Known Broken](#embedded-mode--known-broken) for details. Do not use
embedded mode for projects that push to `dolt.cognovis.de`.

> **If a project is currently on embedded mode**: migrate it back to shared-server mode.
> See [Migrate Embedded to Shared-Server](#migrate-embedded-to-shared-server).

### Auth Layers

There are **two distinct auth contexts**:

| Context | User | Password | Purpose |
|---------|------|----------|---------|
| **Local SQL** | `root` | none | Connect to local shared Dolt server |
| **Remote push/pull** | `__DOLT__grpc_username` in `repo_state.json` | `DOLT_REMOTE_PASSWORD` env var | Auth against dolt.cognovis.de |

The remote username is stored per-database in `.dolt/repo_state.json` under
`remotes.origin.params.__DOLT__grpc_username`. The password comes from the
`DOLT_REMOTE_PASSWORD` environment variable (set in `~/.zshenv`).

**Note**: `DOLT_REMOTE_USER` is NOT an official Dolt env var — only `DOLT_REMOTE_PASSWORD` is.

### DOLT_CLONE Auth Gotcha

`DOLT_CLONE()` does NOT read env vars for the username — it defaults to `root` and fails. Pass `--user` explicitly:
```sql
-- WRONG: fails with "Access denied for user 'root'"
CALL DOLT_CLONE('https://dolt.cognovis.de/beads_mira');

-- CORRECT
CALL DOLT_CLONE('--user', 'malte', 'https://dolt.cognovis.de/beads_mira');
```

### Dolt CLI Global Flags

Global flags go **BEFORE** the subcommand:
```bash
# CORRECT
dolt --host 127.0.0.1 --port 3308 --no-tls sql -q "SELECT 1"

# WRONG — "unknown option"
dolt sql --host 127.0.0.1 -q "SELECT 1"
```

Local server has no TLS → `--no-tls` required. Local `root` has no password.
macOS has no `mysql` client → use `dolt --host ... sql` instead.

## Our Setup

| Component | Location | Purpose |
|-----------|----------|---------|
| **Shared Dolt server** (recommended) | `~/.beads/shared-server/dolt/` | `bd init --shared-server` |
| **Embedded Dolt** (broken, do not use) | `.beads/embeddeddolt/<db>/` per project | `bd init` (v1.0.0+) |
| **Remote** | `dolt.cognovis.de` (Hetzner VPS, Caddy TLS → h2c) | Dolt RemoteAPI |
| **Auth** | `__DOLT__grpc_username` in repo_state.json + `DOLT_REMOTE_PASSWORD` env var | Remote push/pull |

All projects should use shared-server mode. Embedded mode has a known remotesapi bug
(see [Embedded Mode — Known Broken](#embedded-mode--known-broken)).

**Red flags** (embedded mode):
- `repo_state.json` has empty `params: {}` → auth fails with "Access denied for user 'root'"
- `.beads/embeddeddolt/<db>` is empty or missing `.dolt/` → need to clone from remote
- `metadata.json` has `dolt_mode: "server"` but no shared server running → mismatch

**Red flags** (shared-server mode):
- Missing `dolt.shared-server: true` in `.beads/config.yaml`
- Missing `"dolt_mode": "server"` in `metadata.json` (required since bd 0.63.3)
- `metadata.json` contains stale fields: `dolt_server_port`, `backend`, or `database`
- A dolt process running from `.beads/dolt/` instead of `~/.beads/shared-server/dolt/`

> **Not a red flag anymore**: `.beads/dolt-server.port` exists in shared-server mode —
> bd 1.0.0+ writes it as runtime state on each invocation (gitignored). Deleting it is
> harmless; it will be recreated on the next `bd` call. Only worry about it if bd is
> using the port value to connect somewhere wrong (check `bd dolt show`).

## Target State

### Shared-Server Mode (recommended)

#### `.beads/metadata.json`
```json
{
  "dolt_mode": "server",
  "dolt_database": "<prefix>",
  "project_id": "<uuid>"
}
```

#### `.beads/config.yaml`
```yaml
dolt.shared-server: true
```

No port file needed — `bd` manages the port automatically.

## Workflows

### Embedded Mode — Known Broken

> **DO NOT USE embedded mode** for projects pushing to `dolt.cognovis.de`. Migrate to
> shared-server mode instead.

**Problem**: Embedded mode pushes via remotesapi (HTTPS). Every remotesapi push dirties
the remote SQL server's working set (phantom row deletes in `events` and `issues` tables),
causing the next push to fail with `"target has uncommitted changes"`. This happens even
with Dolt v1.85.0 which supposedly fixed related issues (#10727, #10731).

**Root cause**: The remotesapi write updates HEAD on the remote, but the SQL server's
cached working set becomes stale — it sees a diff between its cached working set root
hash and the new HEAD, reporting phantom changes. This is a Dolt bug that does not
affect SQL-protocol pushes (shared-server mode).

**Symptoms**:
- Every second `bd dolt push` fails with `"target has uncommitted changes"`
- `dolt_diff_stat('HEAD', 'WORKING')` on remote shows 1 row deleted from tables
- Committing on remote fixes it temporarily but it recurs on next push
- Dropping `schema_migrations`, clearing `dolt_ignore`, resetting working set — none of
  these permanently fix it
- Even a freshly initialized remote DB exhibits the same behavior

**Workarounds that DON'T work permanently**:
- `CALL dolt_checkout('.')` on remote — fixes one push, breaks again on next
- Dropping `schema_migrations` table — unrelated to the actual cause
- Clearing `dolt_ignore` entries — unrelated to the actual cause
- Moving SQL listener to unused port — SQL engine still loads all DBs on startup

**The only fix**: Migrate to shared-server mode (SQL protocol push, not remotesapi).

### Migrate Embedded to Shared-Server

**When**: Project is on embedded mode and experiencing the remotesapi dirty working set
bug (every second push fails with "target has uncommitted changes").

**Prerequisites**: Data already on remote at `dolt.cognovis.de/<db_name>`.

#### Step 1: Push current data to remote (force if needed)

```bash
bd dolt push --force  # Force-push to ensure remote has latest local data
```

#### Step 2: Switch config to shared-server mode

Edit `.beads/metadata.json` — change `dolt_mode` to `"server"`:
```json
{
  "dolt_mode": "server",
  "dolt_database": "<prefix>",
  "project_id": "<uuid>"
}
```

Edit `.beads/config.yaml` — set shared-server to true:
```yaml
dolt.shared-server: true
```

#### Step 3: Verify shared server is running

```bash
bd dolt show  # Should show "Mode: shared server" and "Server connection OK"
```

If the DB doesn't exist in the shared server yet:
```bash
# Clone from remote into the shared server
dolt --host 127.0.0.1 --port 3308 --no-tls sql -q \
  "CALL DOLT_CLONE('--user', 'malte', 'https://dolt.cognovis.de/<db_name>')"
```

#### Step 4: Add SQL remote (if missing)

```bash
bd dolt remote list  # Check if origin shows [SQL + CLI]
# If it shows [CLI only]:
bd dolt remote add origin https://dolt.cognovis.de/<db_name>
```

#### Step 5: Sync and verify

```bash
bd dolt pull        # Pull latest from remote
bd list --all       # Verify all issues are present
bd dolt push        # Should succeed without force
# Test consecutive pushes:
bd create --title="push test" --type=task --priority=4
bd dolt push        # Should also succeed
bd close <test-id> --reason="test"
bd dolt push        # Third consecutive push — should still work
```

#### Step 6: Clean up embedded artifacts

After verifying everything works:
```bash
rm -rf .beads/embeddeddolt
```

### Embedded Mode Fallback (since 0.63.3)

**Symptom**: `bd dolt show/push/pull/test` returns `Error: 'bd dolt ...' is not supported in
embedded mode (no Dolt server)` — even though `config.yaml` has `dolt.shared-server: true`.

**Root cause**: beads 0.63.3 made embedded mode the default. The `dolt.shared-server: true`
config setting alone is no longer sufficient. `bd` now requires `"dolt_mode": "server"` in
`metadata.json` to use shared-server mode. Without it, `bd` falls back to embedded mode and
creates a `.beads/embeddeddolt/` directory.

**Fix**:

1. Set `dolt_mode` in metadata.json:
```bash
cat .beads/metadata.json
# Add "dolt_mode": "server" if missing
```

2. Remove embedded mode artifacts:
```bash
rm -r .beads/embeddeddolt .beads/dolt-server.port 2>/dev/null
```

3. Verify:
```bash
bd dolt show    # Should show "Mode: shared server" and "Server connection OK"
bd dolt pull    # Should pull from remote
bd list --all   # Should show issues
```

**Note**: `bd init --shared-server --force` does NOT reliably set `dolt_mode: "server"` in
0.63.3 — it may still create embedded mode. Manual metadata.json edit is the reliable fix.

### New Project Setup

```bash
cd /path/to/project && bd init --shared-server --prefix <name>

# Create remote DB (if not exists) — MUST be owned by dolt user, not root
ssh dolt-server "cd /var/lib/dolt && sudo -u dolt mkdir -p beads_<name> && cd beads_<name> && sudo -u dolt /usr/local/bin/dolt init"

# Fix file permissions if needed (if mkdir was run as root not dolt)
ssh dolt-server "chown -R dolt:dolt /var/lib/dolt/beads_<name>"

# Restart remote Dolt server so it discovers the new DB
ssh dolt-server "systemctl restart dolt-server && sleep 3 && systemctl is-active dolt-server"

# Drop the local DB that bd init created (wrong name, no auth), then clone from remote.
# DOLT_CLONE automatically sets __DOLT__grpc_username in the SQL remote — no manual fix needed.
dolt --host 127.0.0.1 --port 3308 --no-tls sql -q "DROP DATABASE IF EXISTS <name>; CALL DOLT_CLONE('--user', 'malte', 'https://dolt.cognovis.de/beads_<name>');"

# Update metadata.json to point to the cloned DB name (beads_<name>)
python3 -c "
import json
path = '.beads/metadata.json'
d = json.load(open(path))
d = {k: v for k, v in d.items() if k in ('dolt_mode', 'dolt_database', 'project_id')}
d['dolt_database'] = 'beads_<name>'
json.dump(d, open(path, 'w'), indent=2)
"

bd dolt pull && bd dolt push --force
```

**Setup Checklist:**
1. Always use `--shared-server` flag (embedded mode is broken for remote push)
2. Create remote dir as `dolt` user — `chown -R dolt:dolt` if created as root; wrong permissions crash the remote server on restart
3. **Restart remote Dolt server** after creating the DB — it won't expose the new DB via RemoteAPI until restarted
4. **Use `DOLT_CLONE` not `bd dolt remote add`** to create the local shared-server DB — clone automatically sets `__DOLT__grpc_username` in params; `bd dolt remote add` does NOT
5. **Drop the `bd init`-created local DB** before cloning — `bd init` creates `<name>` (without `beads_` prefix), but the remote is `beads_<name>`; after clone, update `metadata.json` to `beads_<name>`
6. **Set issue prefix in DB** — `bd config set issue_prefix <PREFIX>`; the `issue-prefix` in `config.yaml` is NOT read for this; without it, all `bd create/update` commands fail with "issue_prefix config is missing"
7. First push to a brand-new empty remote may require `--force` (diverged init histories)
8. Verify `metadata.json` has `"dolt_mode": "server"` and correct `dolt_database` after setup
9. Run `bd prime` after compaction, clear, or new session

### Fix Existing Misconfigured Project

```bash
# Option A: Re-init with shared-server (preserves data if DB name matches)
bd init --shared-server --database <existing_db> --prefix <name> --force

# Option B: Manual fix
bd dolt stop 2>/dev/null
rm -f .beads/dolt-server.port
echo "dolt.shared-server: true" >> .beads/config.yaml
# Clean metadata.json — keep only dolt_database and project_id
python3 -c "
import json
d=json.load(open('.beads/metadata.json'))
keep = {k:v for k,v in d.items() if k in ('dolt_database','project_id') and v}
json.dump(keep, open('.beads/metadata.json','w'), indent=2)
"
rm -f .beads/daemon.log .beads/daemon.pid .beads/daemon.lock \
      .beads/bd.sock .beads/bd.sock.startlock .beads/ephemeral.sqlite3 \
      .beads/interactions.jsonl .beads/.jsonl.lock .beads/sync-state.json \
      .beads/dolt-server.lock .beads/dolt-config.log .beads/dolt-server.log \
      .beads/beads.db-migrated .beads/.migration-hint-ts
bd doctor --fix --yes
bd dolt test && bd dolt push
```

### Diagnose Push Failures

```bash
bd dolt show                    # Connection + remotes
bd dolt remote list             # Should show origin with [SQL + CLI] or [SQL only]
```

| Error | Cause | Fix |
|-------|-------|-----|
| `Access denied for user 'root'` | Missing `__DOLT__grpc_username` in repo_state.json | Set it manually (see Auth Layers) or re-clone |
| `Access denied for user 'X'` | Wrong/missing `DOLT_REMOTE_PASSWORD` env var | Check `~/.zshenv` |
| `no common ancestor` | Local and remote diverged | [Re-Clone Local Database](#re-clone-local-database) |
| `Merge conflict detected` | Same rows modified | [Resolve Pull Merge Conflicts](#resolve-pull-merge-conflicts) |
| `database not found` | Remote DB missing | [Create Remote DB](#create-remote-db) |
| `TLS handshake failed` | Caddy issue | `ssh dolt-server "systemctl status caddy"` |
| `syntax error near '-'` | Hyphens in DB name | Use backtick quoting: `` USE `name` `` |
| `[CLI only]` in remote list | SQL remote missing | `bd dolt remote add origin <url>` |
| Server connection failed | Shared server not running | `bd dolt start` |

### Resolve Pull Merge Conflicts

```bash
# 1. Check conflicts
ssh dolt-server "cd /var/lib/dolt && /usr/local/bin/dolt sql -q \"
USE <db_name>; SELECT * FROM dolt_conflicts;\""

# 2. Resolve on remote (--ours keeps remote version)
ssh dolt-server "cd /var/lib/dolt && /usr/local/bin/dolt sql -q \"
USE <db_name>;
SET autocommit = 0;
SET @@dolt_allow_commit_conflicts = 1;
CALL DOLT_MERGE('<branch>');
CALL DOLT_CONFLICTS_RESOLVE('--ours', '<table>');
CALL DOLT_COMMIT('-am', 'merge: resolve conflicts');\""

# 3. If too diverged → Re-Clone Local Database (below)
```

### Journal Corruption Recovery

**Symptom**: Server fails to start with `invalid journal record length` or `corrupted journal`.
The error does NOT tell you WHICH database is corrupt — Dolt loads all subdirectories and fails
on the first corrupt one.

#### Step 1: Try `fsck` on the suspected DB

```bash
bd dolt stop
cd ~/.beads/shared-server/dolt/<db_name>
dolt fsck --revive-journal-with-data-loss
```

The `--revive-journal-with-data-loss` flag is misleadingly named — it does NOT destroy data. It:
1. Saves a backup of the corrupt journal file
2. Revives the journal from data already on disk
3. Allows the server to start normally

If `fsck` says "no data loss detected" but the server still won't start, the corrupt DB is a
different one. Proceed to Step 2.

#### Step 2: Isolate the corrupt database

Dolt loads ALL subdirectories in its data dir as databases. To find the corrupt one, move
databases out and test.

**CRITICAL**: Move databases OUTSIDE `~/.beads/shared-server/dolt/`, not into a subdirectory
within it. Dolt recursively scans subdirectories — a `quarantine/` folder inside `dolt/` still
gets loaded.

```bash
bd dolt stop

# Create quarantine OUTSIDE the dolt data dir
mkdir -p ~/.beads/shared-server/quarantine

# Move suspected DB out
mv ~/.beads/shared-server/dolt/<suspect_db> ~/.beads/shared-server/quarantine/
bd dolt start
```

If the server starts → that DB was corrupt. If not → move it back, try the next suspect.

**Prioritize by suspicion**: Check journal file sizes to match the error offset:
```bash
for db in ~/.beads/shared-server/dolt/*/; do
  j="$db.dolt/noms/vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv"
  [ -f "$j" ] && echo "$(basename $db): $(stat -f%z "$j") bytes"
done
```

The error offset (e.g. `offset 5592351`) hints at which DB — compare with journal sizes.

#### Step 3: If the root `.dolt` is also corrupted

After a hard kill, the root `.dolt/noms/` may also be damaged (`root hash doesn't exist`).
Fix by re-initializing:

```bash
bd dolt stop
mv ~/.beads/shared-server/dolt/.dolt ~/.beads/shared-server/dolt/.dolt.bak
cd ~/.beads/shared-server/dolt && dolt init
bd dolt start
```

This is safe — individual DB data lives in their own `.dolt/` subdirectories.

#### Step 4: Recover or delete the corrupt DB

- **If the DB exists on remote**: delete locally, re-clone (see [Re-Clone Local Database](#re-clone-local-database))
- **If it's a duplicate** (e.g. `pvs` duplicating `beads_pvs`): delete it
- **If it's an old backup** (e.g. `beads_mira.pre-recovery`): delete it
- **After cleanup**: move all quarantined DBs back and verify `bd dolt start` succeeds

Check for duplicates by inspecting the remote URL:
```bash
cat ~/.beads/shared-server/quarantine/<db>/.dolt/repo_state.json | grep url
```

#### Common causes of journal corruption

- **`pkill -f "dolt sql-server"`** — NEVER do this. Always use `bd dolt stop`.
- **Machine crash / power loss** during write
- **Multiple Dolt processes** writing to the same data directory

### Bead Disappears After Migration

If a bead is missing after shared-server migration (shows in `bd list` on remote but not locally):

```bash
# 1. Check if bead exists on remote
bd dolt pull
bd list --all | grep <bead-id>

# 2. If still missing: direct SQL INSERT from remote data
# Get the bead data from remote
dolt --host 127.0.0.1 --port 3308 --no-tls sql -q \
  "USE beads_mira; SELECT * FROM issues WHERE id = '<bead-id>'"

# 3. If the row is there but bd list doesn't show it, the local branch may be behind
bd dolt pull  # retry after ensuring clean pull
```

This happens when the local DB was re-initialized during migration and the pull didn't fully sync.

### Re-Clone Local Database

When local DB is missing, corrupted, or too diverged.

**Embedded mode** (v1.0.0+):
```bash
# 1. Remove corrupted DB
rm -rf .beads/embeddeddolt/<db_name>

# 2. Clone from remote
cd .beads/embeddeddolt
dolt clone --user malte https://dolt.cognovis.de/<db_name>

# 3. Fix auth in repo_state.json (add __DOLT__grpc_username: malte)
# See "Target State > Embedded Mode" for the full JSON structure

# 4. Verify
bd stats && bd dolt push
```

**Shared-server mode** (legacy):
```bash
# 1. Check if DB exists in shared server
ls ~/.beads/shared-server/dolt/<db_name> 2>/dev/null && echo "EXISTS" || echo "MISSING"

# 2. Drop corrupted DB (if it exists) — get port from bd dolt show
dolt --host 127.0.0.1 --port 3308 --no-tls sql -q "DROP DATABASE \`<db_name>\`"

# 3. Clone — must pass --user explicitly (DOLT_CLONE ignores env vars)
dolt --host 127.0.0.1 --port 3308 --no-tls sql -q \
  "CALL DOLT_CLONE('--user', 'malte', 'https://dolt.cognovis.de/<db_name>')"

# 4. Verify
bd dolt pull && bd dolt show && bd list
```

**Fallback** (server not running):
```bash
cd ~/.beads/shared-server/dolt
dolt clone --user malte https://dolt.cognovis.de/<db_name>
```

### Create Remote DB

```bash
ssh dolt-server "ls /var/lib/dolt/" | grep <db_name>
# If missing:
ssh dolt-server "cd /var/lib/dolt && mkdir -p <db_name> && cd <db_name> && /usr/local/bin/dolt init"
```

Remote server: `ssh dolt-server` (Hetzner VPS, 116.202.111.75).
Config: `/var/lib/dolt/config.yaml`, databases directly in `/var/lib/dolt/`.
Backup: Daily cron at 3:00 AM, 7-day rotation, `/var/backups/dolt/`.

### Remote Recovery via Reflog

Last resort when remote data was accidentally overwritten:

```bash
# 1. Inspect reflog for last good commit
ssh dolt-server "cd /var/lib/dolt && /usr/local/bin/dolt sql -q \"
USE <db_name>;
SELECT ref, commit_hash, commit_message FROM dolt_reflog('main') LIMIT 20;\""

# 2. Reset main to good commit
ssh dolt-server "cd /var/lib/dolt && /usr/local/bin/dolt sql -q \"
USE <db_name>;
CALL DOLT_RESET('--hard', '<good_commit_hash>');\""

# 3. Re-import any local-only issues via dolt table import
# Export from local: dolt sql -r csv -q "SELECT * FROM issues WHERE ..."
# Import on remote or re-clone locally

# 4. Re-clone locally (see Re-Clone Local Database above)
```

**Note**: If schema has changed between commits (e.g. bigint→UUID migration from beads upgrade),
merging branches will fail with "different primary keys". Use `DOLT_RESET` instead of merge,
then re-import missing rows via CSV.

## Pitfalls

- **NEVER `pkill` the Dolt server**: `pkill -f "dolt sql-server"` corrupts journal files. Always `bd dolt stop`. This is the #1 cause of journal corruption.
- **`DOLT_REMOTE_USER` is fake**: Not an official Dolt env var. Only `DOLT_REMOTE_PASSWORD` works. Username comes from `__DOLT__grpc_username` in `repo_state.json`
- **DOLT_CLONE uses `root`**: Always pass `'--user', 'malte'` explicitly — env vars are ignored
- **CLI flag order**: `--host`/`--port`/`--no-tls` go BEFORE `sql` subcommand, not after
- **No TLS locally**: Local server needs `--no-tls` flag or you get "TLS requested but not supported"
- **Local = `root` only**: Only `root` (no password) exists locally. `malte` is remote-only
- **No `mysql` on macOS**: Use `dolt --host ... sql` instead
- **`cd /var/lib/dolt` on remote**: Always cd there first — `dolt sql` from `/root` hits empty instance
- **jq in zsh**: `!=` in jq gets mangled. Use `bash -c '...'` for jq with `!=`
- **Remote URL**: `https://dolt.cognovis.de/<db>` only. Old `http://192.168.60.30:8080` is decommissioned
- **First push fails**: New remote DB has no commit history — first push may need `--force` (ONLY for brand-new empty remotes, with user confirmation)
- **NEVER force-push on shared remotes**: Destroys other users' commits. Re-clone locally instead
- **Caddy TLS proxy**: Uses `transport http { versions 1.1 h2c }` — the `1.1` is critical for Dolt's dual-protocol. Source: [dolthub/dolt#9332](https://github.com/dolthub/dolt/issues/9332)
- **Schema migration on bd upgrade**: `bd` auto-migrates schemas (e.g. comments.id bigint→UUID). This creates commits that can't merge with pre-migration branches. All team members must be on the same `bd` version.
- **Embedded mode default (0.63.3+)**: `bd` defaults to embedded mode. `config.yaml` `dolt.shared-server: true` alone is NOT sufficient — you MUST also have `"dolt_mode": "server"` in `metadata.json`. Without it, `bd` creates `.beads/embeddeddolt/` and all `bd dolt` commands fail with "not supported in embedded mode".
- **`bd init --shared-server` unreliable (0.63.3)**: Even with `--shared-server` flag, `bd init` may still create embedded mode. Always verify metadata.json after init and manually add `"dolt_mode": "server"` if missing.
- **Embedded pull panics on empty DB (v1.0.0)**: `bd dolt pull` into a freshly initialized empty embedded DB crashes with nil pointer dereference. Use `dolt clone` instead for initial data load.
- **Embedded init sets wrong remote (v1.0.0)**: `bd init` sets the Dolt remote to the git repo URL. Always fix with `bd dolt remote remove origin && bd dolt remote add origin https://dolt.cognovis.de/<db>`.
- **Embedded auth defaults to `root`**: After `dolt clone` or `bd init`, `repo_state.json` has empty `params: {}`. Must add `__DOLT__grpc_username` manually or push/pull fails with "Access denied for user 'root'".
- **Shared-server `bd dolt remote add` doesn't set auth**: In shared-server mode, `bd dolt remote add` does NOT write `__DOLT__grpc_username` to `~/.beads/shared-server/dolt/<db>/.dolt/repo_state.json`. After adding a remote, always set it manually: `python3 -c "import json; path='~/.beads/shared-server/dolt/<db>/.dolt/repo_state.json'; d=json.load(open(path)); d['remotes']['origin']['params']['__DOLT__grpc_username']='malte'; json.dump(d,open(path,'w'),indent=2)"`
- **`bd dolt show` / `bd doctor` unsupported in embedded (v1.0.0)**: Cosmetic limitation. Use `bd stats` and `bd dolt push/pull` to verify health instead.
- **`schema_migrations` table causes remote dirty state**: `bd` v1.0.0 creates a `schema_migrations` table in embedded mode. The Dolt SQL server on the remote auto-deletes it from WORKING on every startup/push, causing permanent "target has uncommitted changes" errors. Fix: drop the table locally (`DROP TABLE schema_migrations` + `DOLT_COMMIT`), verify both sides have same issue count, then `bd dolt push --force` once. `bd` works fine without it after initial migrations.
- **Old shared Dolt server may still be running**: After migrating to embedded mode, check `ps aux | grep dolt` for a stale `dolt sql-server` on port 3308. Kill it — it's no longer needed and holds a duplicate copy of the DB pointing to the same remote.

## Infrastructure Reference

- **Shared server** (recommended): Managed by `bd`, data in `~/.beads/shared-server/dolt/`
- **Embedded Dolt** (broken, do not use): Per-project in `.beads/embeddeddolt/<db>/`
- **Remote**: `dolt.cognovis.de` (116.202.111.75), SSH: `ssh dolt-server` (alias `erp4projects`)
- **Remote config**: `/var/lib/dolt/config.yaml`, databases directly in `/var/lib/dolt/`
- **Remote backup**: Daily cron 3:00 AM → `/var/backups/dolt/`, 7-day rotation, script `/usr/local/bin/dolt-backup.sh`
- **Remote Caddy**: `servers :443 { protocols h1 h2 h2c }` + `transport http { versions 1.1 h2c }`
- **Remote users**: `ssh dolt-server "cd /var/lib/dolt && dolt sql -q 'SELECT user, host FROM mysql.user;'"`
- **All beads installations**: `find ~/code -maxdepth 4 -name ".beads" -type d`
- **Full command reference**: `bd dolt --help`

## Reference Files

- `references/fleet-cleanup.md` — Legacy bash script for fixing installations
- `references/team-onboarding.md` — Step-by-step for new team members
