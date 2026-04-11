# Team Member Onboarding

For a new team member to use `bd dolt push/pull`:

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

1. Install Dolt: `brew install dolt`

2. Create central data dir: `mkdir -p ~/.dolt-data`

3. Create server config at `~/.dolt-data/config.yaml`:
```yaml
listener:
  host: 127.0.0.1
  port: 3307
  allow_cleartext_passwords: true
data_dir: /Users/USERNAME/.dolt-data
remotesapi:
  port: 0
system_variables:
  default_authentication_plugin: mysql_native_password
```

4. Create LaunchAgent at `~/Library/LaunchAgents/com.beads.dolt-server.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.beads.dolt-server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/dolt</string>
        <string>sql-server</string>
        <string>--config</string>
        <string>/Users/USERNAME/.dolt-data/config.yaml</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>DOLT_REMOTE_USER</key>
        <string>newuser</string>
        <key>DOLT_REMOTE_PASSWORD</key>
        <string>SECURE_PASSWORD</string>
    </dict>
    <key>WorkingDirectory</key>
    <string>/Users/USERNAME/.dolt-data</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/USERNAME/.dolt-data/server.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/USERNAME/.dolt-data/server.err</string>
</dict>
</plist>
```

5. Load the agent: `launchctl load ~/Library/LaunchAgents/com.beads.dolt-server.plist`

6. Add credentials to `~/.zshrc` (uses 1Password runtime injection):
```bash
export DOLT_REMOTE_USER="newuser"
export DOLT_REMOTE_PASSWORD="$(op read 'op://API Keys/Dolt Remote - newuser/password' 2>/dev/null)"
```

7. Verify: `bd dolt test && bd dolt push`
