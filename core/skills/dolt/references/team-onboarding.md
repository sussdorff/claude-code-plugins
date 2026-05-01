# Team Member Onboarding

For a new team member to use `bd dolt push/pull`.

## On the remote server (one-time, done by admin)

```bash
ssh erp4projects "cd /var/lib/dolt/data && dolt sql -q \"
  CREATE USER 'newuser'@'%' IDENTIFIED BY 'SECURE_PASSWORD';
  GRANT SUPER ON *.* TO 'newuser'@'%';
  GRANT CLONE_ADMIN ON *.* TO 'newuser'@'%';
  FLUSH PRIVILEGES;
\""
```

Store credentials in 1Password: vault "API Keys", title "Dolt Remote - newuser".

## On the team member's Mac

```bash
# 1. Install Dolt and beads
brew install dolt beads

# 2. Tell Homebrew's dolt where to put data (one line in /opt/homebrew/etc/dolt/config.yaml)
echo 'data_dir: /Users/USERNAME/.dolt-data' >> /opt/homebrew/etc/dolt/config.yaml
# Replace USERNAME with the actual macOS user.

# 3. Set up shell env (~/.zshenv)
cat >> ~/.zshenv <<'EOF'

# Dolt remote auth (1Password runtime injection)
export DOLT_REMOTE_PASSWORD="$(op read 'op://API Keys/Dolt Remote - newuser/password' 2>/dev/null)"

# bd connects to the brew-managed Dolt server
export BEADS_DOLT_SERVER_PORT=3306
EOF
exec zsh   # or open a new shell

# 4. Start Dolt as a launchd-managed service (auto-starts at login, keep_alive on crash)
brew services start dolt
brew services info dolt    # Verify Running: true

# 5. Clone the project DBs you need (DOLT_CLONE ignores env vars — pass --user explicitly)
dolt --host 127.0.0.1 --port 3306 --no-tls sql -q \
  "CALL DOLT_CLONE('--user', 'newuser', 'https://dolt.cognovis.de/beads_<project>')"
brew services restart dolt   # Dolt indexes data_dir at start; restart to see the new DB

# 6. Verify
cd ~/code/<project>
bd dolt show     # Should show "Server connection OK"
bd list          # Should list the project's issues
```

## Notes

- macOS does not have systemd; `brew services` is the canonical replacement and is what the
  Homebrew dolt formula ships with.
- `DOLT_REMOTE_USER` is **not** an official Dolt env var — only `DOLT_REMOTE_PASSWORD` is read.
  The username comes from `__DOLT__grpc_username` in `<db>/.dolt/repo_state.json`, which
  `DOLT_CLONE --user newuser` writes automatically.
- Why `~/.dolt-data/` and not Homebrew's default `/opt/homebrew/var/dolt/`? Data in `$HOME` is
  picked up by Time Machine / iCloud / `rsync $HOME` automatically, and survives
  `brew uninstall dolt` (Homebrew doesn't guarantee `var/<formula>/` preservation on uninstall).
