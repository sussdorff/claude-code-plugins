# Migrate from bd-managed shared server to brew services

For machines still on the legacy `bd dolt start` pattern with data in
`~/.beads/shared-server/dolt/` and port 3308. One-time migration per machine.

```bash
# 1. Stop the bd-managed server
bd dolt stop

# 2. Copy data into Homebrew's location.
#    Do NOT mv across home paths — the dcg sandbox blocks it. Use rsync.
rsync -a ~/.beads/shared-server/dolt/  ~/.dolt-data/
diff <(ls ~/.beads/shared-server/dolt/) <(ls ~/.dolt-data/)   # should be empty

# 3. Set Dolt's data_dir override (one line in /opt/homebrew/etc/dolt/config.yaml)
echo 'data_dir: /Users/malte/.dolt-data' >> /opt/homebrew/etc/dolt/config.yaml

# 4. Set the port env var fleet-wide
echo 'export BEADS_DOLT_SERVER_PORT=3306' >> ~/.zshenv
exec zsh   # or open a new shell

# 5. Start the brew service
brew services start dolt

# 6. Clean up bd's stale runtime files (so bd dolt start/stop can't interfere)
rm ~/.beads/shared-server/dolt-server.{lock,log,pid,port} 2>/dev/null

# 7. Verify in any project
cd <some bd project> && bd list
# `Info: updating port file 3308 → 3306` is normal — bd auto-syncs the project port file.

# 8. After a soak period, free disk by removing the source copy
#    Use `dcg allow-once rm -rf ~/.beads/shared-server/dolt` (~793 MB)
```

## Why brew services?

- `keep_alive: true` — auto-restart on crash, auto-start at login (no LaunchAgent to maintain).
- Standard Homebrew lifecycle: `brew services start/stop/restart/info dolt`.
- Config in `/opt/homebrew/etc/dolt/config.yaml` is preserved across `brew upgrade dolt`.
- Logs at `/opt/homebrew/var/log/dolt.log` (errors at `dolt.error.log`).
- macOS does not have systemd; brew services is the canonical replacement.

## Why `~/.dolt-data/` (not Homebrew's `working_dir /opt/homebrew/var/dolt/`)?

- Data in $HOME is included in Time Machine / iCloud / rsync home dir.
- Survives `brew uninstall dolt` (Homebrew's `var/<formula>/` is not guaranteed preserve).
- Setting `data_dir` is the documented Dolt extension API, not a hack — the shipped
  config has `# data_dir: .` as an explicit override hint.
