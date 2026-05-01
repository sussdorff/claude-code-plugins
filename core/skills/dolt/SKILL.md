---
name: dolt
description: >
  Troubleshoot beads Dolt failures: `bd dolt` push/pull errors, merge conflicts,
  embedded/shared-server mode problems, remote auth issues, local DB recovery, re-clone,
  reflog restore, broken `.beads` Dolt config, and brew-services Dolt lifecycle. Use
  whenever beads sync or Dolt infrastructure is failing — symptoms like "beads do not
  sync", "cannot push issues", "no common ancestor", "not supported in embedded mode",
  "Dolt server unreachable", or "lost local database". Read the beads changelog first.
  Do not use for normal beads tracking (`bd create/ready/close`), standalone Dolt
  databases, or regular git push/pull.
requires_standards: [english-only]
---

# dolt

> **Version gate**: trust `bd --help` and the CHANGELOG over this document if they
> disagree. Run `bd --version` and read recent CHANGELOG before diagnosing — version
> upgrades change mode detection logic and metadata schema.
>
> ```bash
> bd --version
> cat /opt/homebrew/Cellar/beads/$(bd --version | awk '{print $3}')/CHANGELOG.md | head -120
> ```

## Architecture

`brew services start dolt` runs Dolt at login (launchd, `keep_alive: true`). It reads
`/opt/homebrew/etc/dolt/config.yaml`, which sets `data_dir: /Users/malte/.dolt-data` —
the only override; everything else stays at Dolt defaults (port 3306, `root` no password,
no TLS). bd connects via `BEADS_DOLT_SERVER_PORT=3306` in `~/.zshenv` (fleet-wide). Each
project has `dolt.shared-server: true` in `.beads/config.yaml` and `"dolt_mode": "server"`
in `.beads/metadata.json`. Push/pull goes via SQL protocol — does not trigger the embedded
remotesapi dirty-working-set bug.

**Lifecycle is owned by `brew services`, not bd.** Do NOT use `bd dolt start` /
`bd dolt stop` — they would conflict with the brew-managed process and `keep_alive`.

## Golden Rules

**Push pattern**: `bd dolt pull && bd dolt push --force`. Dolt
[#10807](https://github.com/dolthub/dolt/issues/10807) dirties the remote working set on
every push; `--force` overwrites phantom dirty state, NOT commit history. Pull first to
merge others' commits. **Exception**: on `no common ancestor`, do NOT force-push —
[Re-Clone](#re-clone-local-database) instead.

**No raw `dolt` for sync**: never `dolt push/pull/commit` directly — always `bd dolt`. Two
narrow exceptions: `dolt --host 127.0.0.1 --port 3306 --no-tls sql -q "..."` for direct
SQL, and `dolt clone` for initial setup.

**No `pkill`**: corrupts journal files. Use `brew services stop dolt`.

**No embedded mode**: `bd init` (without `--shared-server`) pushes via remotesapi, which
dirties the remote working set on every push regardless of Dolt version. Always
`bd init --shared-server`; verify `metadata.json` has `"dolt_mode": "server"`.

## Quick Triage

```bash
brew services info dolt                       # Server running?
bd dolt show                                  # Connection + remotes
cat .beads/metadata.json                      # dolt_mode + dolt_database
grep dolt .beads/config.yaml                  # shared-server: true?
echo $BEADS_DOLT_SERVER_PORT                  # 3306?
bd stats                                      # Verifies actual DB access
dolt --host 127.0.0.1 --port 3306 --no-tls sql -q "SHOW DATABASES"
```

| Symptom | Go to |
|---------|-------|
| Server not running | `brew services start dolt` |
| Brew started before data was in place | `brew services restart dolt` (Dolt indexes `data_dir` at start) |
| `Dolt server unreachable at 127.0.0.1:3306` | [Server Lifecycle](#server-lifecycle) |
| `database <name> not found` | [Re-Clone Local Database](#re-clone-local-database) |
| `bd dolt push/pull` fails | [Diagnose Push Failures](#diagnose-push-failures) |
| `corrupted journal` / `invalid journal record length` | [Journal Corruption Recovery](#journal-corruption-recovery) |
| `no common ancestor` | [Re-Clone Local Database](#re-clone-local-database) (do NOT force-push) |
| `Merge conflict detected` on pull | [`scripts/resolve-merge-conflicts.sh`](scripts/resolve-merge-conflicts.sh) |
| Remote DB doesn't exist | [Create Remote DB](#create-remote-db) |
| Remote data lost | [`scripts/remote-recovery-reflog.sh`](scripts/remote-recovery-reflog.sh) |
| Project still on legacy `bd dolt start` setup | [`references/migrate-to-brew-services.md`](references/migrate-to-brew-services.md) |
| Project still in embedded mode | [`references/migrate-embedded.md`](references/migrate-embedded.md) |
| New project | [`scripts/new-project-setup.sh`](scripts/new-project-setup.sh) |
| New team member | [`references/team-onboarding.md`](references/team-onboarding.md) |
| Phantom database warnings in `bd doctor` | Cosmetic, [dolthub/dolt#2051](https://github.com/dolthub/dolt/issues/2051). Ignore. |

## Auth Layers

| Context | User | Password | Where |
|---------|------|----------|-------|
| Local SQL | `root` | none | brew-managed dolt sql-server |
| Remote push/pull | `__DOLT__grpc_username` per-DB | `~/.dolt-remote-password` (via LaunchAgent, see below) + `DOLT_REMOTE_PASSWORD` env var | `~/.dolt-data/<db>/.dolt/repo_state.json` + `~/.zshenv` |

Watch out:
- `DOLT_REMOTE_USER` is **not** an official env var — only `DOLT_REMOTE_PASSWORD` is. Username
  must live in `repo_state.json`.
- `DOLT_CLONE()` ignores env vars for username; pass `--user` explicitly:
  ```sql
  CALL DOLT_CLONE('--user', 'malte', 'https://dolt.cognovis.de/beads_<db>');
  ```
- `bd dolt remote add` does NOT write `__DOLT__grpc_username`. After adding, set manually:
  ```bash
  python3 -c "
  import json, sys
  p='/Users/malte/.dolt-data/<db>/.dolt/repo_state.json'
  d=json.load(open(p))
  d['remotes']['origin']['params']['__DOLT__grpc_username']='malte'
  json.dump(d,open(p,'w'),indent=2)"
  ```

### Persistent Auth Setup (macOS — brew-managed dolt)

The brew dolt daemon runs as a user LaunchAgent (`~/Library/LaunchAgents/homebrew.mxcl.dolt.plist`).
launchd does NOT inherit shell env vars (`~/.zshenv`/`~/.zshrc`), so `DOLT_REMOTE_PASSWORD` must be
injected into launchd's global environment via a dedicated LaunchAgent.

**One-time setup (already done on the main workstation):**

```bash
# 1. Store the password securely (from 1Password: vault API Keys, item "Dolt Remote - malte")
echo -n "$DOLT_REMOTE_PASSWORD" > ~/.dolt-remote-password
chmod 600 ~/.dolt-remote-password

# 2. Create ~/Library/LaunchAgents/com.cognovis.dolt-auth.plist with this exact content:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>Label</key>
	<string>com.cognovis.dolt-auth</string>
	<key>ProgramArguments</key>
	<array>
		<string>/bin/bash</string>
		<string>-c</string>
		<string>PW=$(cat /Users/malte/.dolt-remote-password) || { echo "ERROR: cannot read password file" &gt;&amp;2; exit 1; }; [ -n "$PW" ] || { echo "ERROR: password file is empty" &gt;&amp;2; exit 1; }; /bin/launchctl setenv DOLT_REMOTE_PASSWORD "$PW" || { echo "ERROR: launchctl setenv failed" &gt;&amp;2; exit 1; }; /bin/launchctl stop homebrew.mxcl.dolt</string>
	</array>
	<key>RunAtLoad</key>
	<true/>
	<key>StandardErrorPath</key>
	<string>/Users/malte/.dolt-auth.err.log</string>
	<key>StandardOutPath</key>
	<string>/Users/malte/.dolt-auth.log</string>
</dict>
</plist>
```
#    KeepAlive is NOT set — this is a one-shot agent, not a persistent daemon
#    Errors flow to ~/.dolt-auth.err.log; empty/missing password file causes a non-zero exit

# 3. Load it
launchctl load ~/Library/LaunchAgents/com.cognovis.dolt-auth.plist
```

**How it works:**
1. At login, `homebrew.mxcl.dolt` and `com.cognovis.dolt-auth` start in parallel via RunAtLoad. `setenv` is called synchronously before `stop`, ensuring dolt's restarted process inherits the env var — the parallel start of `homebrew.mxcl.dolt` doesn't matter because `stop`+KeepAlive-restart happens after `setenv` completes.
2. Reads password from `~/.dolt-remote-password`
3. Sets `DOLT_REMOTE_PASSWORD` in launchd's global env table via `launchctl setenv`
4. Stops `homebrew.mxcl.dolt` (SIGTERM) → `KeepAlive: true` auto-restarts dolt
5. Restarted dolt inherits `DOLT_REMOTE_PASSWORD` from launchd's global env table

**Why `~/.zshenv` still exports `DOLT_REMOTE_PASSWORD`:**
Direct `dolt` CLI calls (e.g., `dolt push --user=malte` from the terminal) read `DOLT_REMOTE_PASSWORD`
from the shell environment. Keep it in `~/.zshenv` for these cases.
The LaunchAgent handles the daemon's environment separately.

**Note**: `dolt creds` (keypair auth) is for DoltHub only — NOT applicable for self-hosted servers
with username/password auth. The `DOLT_REMOTE_PASSWORD` env var is the only supported mechanism.

**Quickfix (after reboot if LaunchAgent fails or is not yet installed):**
```bash
launchctl setenv DOLT_REMOTE_PASSWORD "$(cat ~/.dolt-remote-password)"
launchctl stop homebrew.mxcl.dolt  # KeepAlive restarts it with new env
```

## Dolt CLI flag order

Global flags go **BEFORE** the subcommand:

```bash
# CORRECT
dolt --host 127.0.0.1 --port 3306 --no-tls sql -q "SELECT 1"
# WRONG — "unknown option"
dolt sql --host 127.0.0.1 -q "SELECT 1"
```

Local server has no TLS (`--no-tls` required) and no password for `root`. macOS has no
`mysql` client — use `dolt --host ... sql` instead.

---

## Server Lifecycle

```bash
brew services start dolt        # Manually start (also auto-starts at login)
brew services stop dolt
brew services restart dolt      # Needed after adding databases to ~/.dolt-data/
brew services info dolt
tail -f /opt/homebrew/var/log/dolt.log
tail -f /opt/homebrew/var/log/dolt.error.log
```

The launchd plist is at `~/Library/LaunchAgents/homebrew.mxcl.dolt.plist` — let Homebrew
manage it.

Config file `/opt/homebrew/etc/dolt/config.yaml` has only one active line; the rest are
commented stubs:

```yaml
data_dir: /Users/malte/.dolt-data
```

Defaults fill the rest (port 3306, host 127.0.0.1, no TLS).

**Critical**: Dolt indexes `data_dir` at process start. Adding a database to `~/.dolt-data/`
while the server is running → invisible until `brew services restart dolt`.

## Diagnose Push Failures

```bash
bd dolt show                    # Connection + remotes
bd dolt remote list             # origin should be [SQL + CLI]
```

| Error | Cause | Fix |
|-------|-------|-----|
| `Dolt server unreachable at 127.0.0.1:3306` | brew services not running | `brew services start dolt` |
| `database <name> not found` | server started before data was copied, or DB really missing | `brew services restart dolt`; if still missing → [Re-Clone](#re-clone-local-database) |
| `Access denied for user 'root'` | Missing `__DOLT__grpc_username` in repo_state.json | Set manually (see [Auth Layers](#auth-layers)) or re-clone |
| `Access denied for user 'malte'` | Wrong/missing `DOLT_REMOTE_PASSWORD` | Check `~/.zshenv`; after reboot also verify daemon env: `launchctl getenv DOLT_REMOTE_PASSWORD` |
| `must set DOLT_REMOTE_PASSWORD` (after reboot) | Brew dolt daemon started before auth LaunchAgent ran | Check: `launchctl list \| grep dolt-auth`; fix: `launchctl load ~/Library/LaunchAgents/com.cognovis.dolt-auth.plist` |
| `target has uncommitted changes` | [dolthub/dolt#10807](https://github.com/dolthub/dolt/issues/10807) | `bd dolt pull && bd dolt push --force` |
| `no common ancestor` | Local & remote diverged | [Re-Clone](#re-clone-local-database) — do NOT force-push |
| `Merge conflict detected` | Same rows modified on both sides | [`scripts/resolve-merge-conflicts.sh`](scripts/resolve-merge-conflicts.sh) |
| `database not found` (remote) | Remote DB missing | [Create Remote DB](#create-remote-db) |
| `TLS handshake failed` | Caddy issue on remote | `ssh dolt-server "systemctl status caddy"` |
| `syntax error near '-'` | Hyphens in DB name in SQL | Use backticks: `` USE `name-with-hyphen` `` |
| `[CLI only]` in remote list | SQL remote missing | `bd dolt remote add origin <url>` (then set auth manually) |

## Re-Clone Local Database

When local DB is missing, corrupted, or too diverged from remote.

```bash
# 1. Stop the server (Dolt locks data dir during clone via DOLT_CLONE doesn't need stop,
#    but a local DB drop does)
brew services stop dolt

# 2. Drop or move corrupted DB
rm -rf ~/.dolt-data/<db_name>     # or move to a backup location

# 3. Restart server with empty target slot
brew services start dolt

# 4. Clone (DOLT_CLONE ignores env vars — pass --user explicitly)
dolt --host 127.0.0.1 --port 3306 --no-tls sql -q \
  "CALL DOLT_CLONE('--user', 'malte', 'https://dolt.cognovis.de/<db_name>')"

# 5. Restart so Dolt indexes the new DB
brew services restart dolt

# 6. Verify
bd dolt show && bd list
```

**Fallback** (server unhealthy): clone via CLI directly into the data dir:

```bash
brew services stop dolt
cd ~/.dolt-data && dolt clone --user malte https://dolt.cognovis.de/<db_name>
brew services start dolt
```

## Journal Corruption Recovery

**Symptom**: server fails to start with `invalid journal record length` / `corrupted journal`.
The error does NOT name the corrupt DB — Dolt loads all subdirs and fails on the first one.

### Step 1: try `fsck` on the suspected DB

```bash
brew services stop dolt
cd ~/.dolt-data/<db_name>
dolt fsck --revive-journal-with-data-loss
brew services start dolt
```

The flag is misleading — it does NOT destroy data. It backs up the corrupt journal, revives
it from on-disk data, and lets the server start.

### Step 2: isolate the corrupt database

If `fsck` says "no data loss detected" but server still won't start, you have the wrong DB.
Move suspects **OUTSIDE** the data dir (Dolt recursively scans subdirs — a `quarantine/`
inside `~/.dolt-data/` would still get loaded).

```bash
brew services stop dolt
mkdir -p ~/.dolt-quarantine
mv ~/.dolt-data/<suspect_db> ~/.dolt-quarantine/   # may need `dcg allow-once`
brew services start dolt    # if it starts → that DB was corrupt
```

Prioritize by suspicion — match the error offset to journal sizes:

```bash
for db in ~/.dolt-data/*/; do
  j="$db.dolt/noms/vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv"
  [ -f "$j" ] && echo "$(basename $db): $(stat -f%z "$j") bytes"
done
```

### Step 3: if root `~/.dolt-data/.dolt` is also corrupted

After a hard kill, the root `.dolt/noms/` may be damaged (`root hash doesn't exist`):

```bash
brew services stop dolt
mv ~/.dolt-data/.dolt ~/.dolt-data/.dolt.bak
cd ~/.dolt-data && dolt init
brew services start dolt
```

Safe — individual DB data lives in their own `.dolt/` subdirs.

### Step 4: recover or delete the corrupt DB

- DB on remote → delete locally, [Re-Clone](#re-clone-local-database).
- Duplicate or stale backup → just delete it.
- Then move all quarantined DBs back and `brew services restart dolt`.

Causes:
- `pkill -f "dolt sql-server"` — never. Always `brew services stop dolt`.
- Machine crash / power loss during write.
- Multiple Dolt processes on the same data dir (don't run `bd dolt start` while brew services is up).

## Create Remote DB

```bash
ssh dolt-server "ls /var/lib/dolt/" | grep <db_name>
# If missing:
ssh dolt-server "cd /var/lib/dolt && sudo -u dolt mkdir -p <db_name> && cd <db_name> && sudo -u dolt /usr/local/bin/dolt init"
ssh dolt-server "chown -R dolt:dolt /var/lib/dolt/<db_name>"
ssh dolt-server "systemctl restart dolt-server && sleep 3 && systemctl is-active dolt-server"
```

Permissions matter — must be owned by the `dolt` user, not root. Restart so RemoteAPI sees
the new DB.

Remote: `dolt.cognovis.de` (Hetzner VPS, 116.202.111.75). SSH alias `dolt-server` /
`erp4projects`. Config `/var/lib/dolt/config.yaml`. Daily backup cron 03:00 →
`/var/backups/dolt/` (7-day rotation).

## Pitfalls

- **Phantom database warnings in `bd doctor`**: cosmetic, [dolthub/dolt#2051](https://github.com/dolthub/dolt/issues/2051). Restart fixes only temporarily; doesn't matter for operation.
- **`pkill` corrupts journals.** Use `brew services stop dolt`. Don't `bd dolt stop` while brew services is running — it'd kill the brew-managed PID.
- **Dolt indexes `data_dir` at start.** Add a DB while running → invisible until restart.
- **`mv` on `~` paths is blocked by dcg sandbox.** Use `rsync -a` + `diff -r` + `rm`, or have user run `mv` manually with `dcg allow-once`.
- **`DOLT_CLONE` defaults to `root`.** Always pass `'--user', 'malte'` — env vars ignored.
- **`bd dolt remote add` does NOT write auth.** Always set `__DOLT__grpc_username` manually.
- **First push to a brand-new empty remote** may need `--force` (diverged init histories). ONLY for empty remotes, with confirmation.
- **NEVER force-push on shared remotes** beyond the dolt#10807 workaround pattern. Re-clone locally instead.
- **Schema migration on bd upgrade**: `bd` auto-migrates schemas (e.g. `comments.id` bigint → UUID). These commits can't merge with pre-migration branches — keep team on the same `bd` version.
- **Caddy on remote** uses `transport http { versions 1.1 h2c }` — the `1.1` is critical for Dolt's dual-protocol ([dolthub/dolt#9332](https://github.com/dolthub/dolt/issues/9332)). Don't simplify.
- **`cd /var/lib/dolt` on remote** before any `dolt sql` — running from `/root` hits an empty instance.
- **Remote URL is `https://dolt.cognovis.de/<db>`** only. Old `http://192.168.60.30:8080` is decommissioned.
- **Hyphens in DB names** require backticks in SQL: `` USE `db-with-hyphen` ``.

## Infrastructure Reference

| Component | Location |
|-----------|----------|
| Dolt server (macOS) | `brew services start dolt` (launchd: `~/Library/LaunchAgents/homebrew.mxcl.dolt.plist`) |
| Local data dir | `~/.dolt-data/` |
| Local config | `/opt/homebrew/etc/dolt/config.yaml` (preserved across `brew upgrade dolt`) |
| Local logs | `/opt/homebrew/var/log/dolt.log`, `dolt.error.log` |
| Local port | 3306 |
| bd port override | `BEADS_DOLT_SERVER_PORT=3306` in `~/.zshenv` |
| Remote | `dolt.cognovis.de` (Hetzner, 116.202.111.75) |
| Remote SSH | `ssh dolt-server` (alias `erp4projects`) |
| Remote config | `/var/lib/dolt/config.yaml` |
| Remote data | databases directly under `/var/lib/dolt/` |
| Remote backup | daily 03:00 cron → `/var/backups/dolt/` (7-day rotation) |
| All bd projects | `find ~/code -maxdepth 4 -name .beads -type d` |
| Full bd commands | `bd dolt --help` |

## Reference Files

- [`references/team-onboarding.md`](references/team-onboarding.md) — new team member setup
- [`references/migrate-to-brew-services.md`](references/migrate-to-brew-services.md) — one-time machine migration from `bd dolt start`
- [`references/migrate-embedded.md`](references/migrate-embedded.md) — legacy embedded mode → shared-server
- [`references/fleet-cleanup.md`](references/fleet-cleanup.md) — bulk-fix legacy installations
- [`scripts/new-project-setup.sh`](scripts/new-project-setup.sh) — `bd init --shared-server` for a new project
- [`scripts/fix-misconfigured.sh`](scripts/fix-misconfigured.sh) — repair drift in an existing project
- [`scripts/sync-verify.sh`](scripts/sync-verify.sh) — consecutive-push verification
- [`scripts/resolve-merge-conflicts.sh`](scripts/resolve-merge-conflicts.sh) — pull conflict resolver
- [`scripts/remote-recovery-reflog.sh`](scripts/remote-recovery-reflog.sh) — last-resort remote restore
