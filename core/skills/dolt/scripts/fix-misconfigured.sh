#!/usr/bin/env bash
# TEMPLATE: Choose ONE of Option A or Option B below. Comment out the other.

# Option A: Re-init with shared-server (preserves data if DB name matches)
bd init --shared-server --database <existing_db> --prefix <name> --force
exit 0

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
