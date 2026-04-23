# Fleet-Wide Cleanup

Save as a bash script to avoid zsh escaping issues with jq:

```bash
#!/bin/bash
# fleet-fix.sh — Run with: bash fleet-fix.sh
for d in $(find ~/code -maxdepth 3 -name ".beads" -type d 2>/dev/null); do
  project=$(dirname "$d")
  pname=$(basename "$project")
  changed=""

  # Fix port file
  if [ "$(cat "$d/dolt-server.port" 2>/dev/null)" != "3307" ]; then
    echo "3307" > "$d/dolt-server.port"
    changed="${changed} port"
  fi

  # Fix data dir (via bd config)
  (cd "$project" && bd config set dolt-data-dir /Users/malte/.dolt-data 2>/dev/null)

  # Clean metadata.json
  if [ -f "$d/metadata.json" ]; then
    has_junk=$(jq 'keys | map(select(. == "backend" or . == "dolt_mode" or . == "dolt_server_port" or . == "database")) | length' "$d/metadata.json" 2>/dev/null)
    if [ "$has_junk" -gt 0 ] 2>/dev/null; then
      tmp=$(mktemp)
      jq '{dolt_database, project_id} | with_entries(select(.value != null))' "$d/metadata.json" > "$tmp" && mv "$tmp" "$d/metadata.json"
      changed="${changed} metadata"
    fi
  fi

  # Remove legacy files
  removed=0
  for f in daemon.log daemon.pid daemon.lock bd.sock bd.sock.startlock ephemeral.sqlite3 \
           interactions.jsonl .jsonl.lock sync-state.json dolt-server.lock dolt-config.log \
           dolt-server.log beads.db-migrated .migration-hint-ts; do
    [ -f "$d/$f" ] && rm -f "$d/$f" && removed=$((removed + 1))
  done
  [ "$removed" -gt 0 ] && changed="${changed} legacy($removed)"

  # Remove local server config
  if [ -f "$d/dolt/config.yaml" ] && grep -q "listener:" "$d/dolt/config.yaml" 2>/dev/null; then
    rm -f "$d/dolt/config.yaml"
    changed="${changed} local-cfg"
  fi

  [ -n "$changed" ] && echo "FIXED $pname:$changed"
done
```
