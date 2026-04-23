#!/usr/bin/env bash
# TEMPLATE: Pass project name as first argument or set NAME below.
# Usage: bash new-project-setup.sh myproject
NAME="${1:-your-project}"  # Replace with actual project prefix or pass as $1

cd /path/to/project && bd init --shared-server --prefix "$NAME"

# Create remote DB (if not exists) — MUST be owned by dolt user, not root
ssh dolt-server "cd /var/lib/dolt && sudo -u dolt mkdir -p beads_$NAME && cd beads_$NAME && sudo -u dolt /usr/local/bin/dolt init"

# Fix file permissions if needed (if mkdir was run as root not dolt)
ssh dolt-server "chown -R dolt:dolt /var/lib/dolt/beads_$NAME"

# Restart remote Dolt server so it discovers the new DB
ssh dolt-server "systemctl restart dolt-server && sleep 3 && systemctl is-active dolt-server"

# Drop the local DB that bd init created (wrong name, no auth), then clone from remote.
# DOLT_CLONE automatically sets __DOLT__grpc_username in the SQL remote — no manual fix needed.
dolt --host 127.0.0.1 --port 3308 --no-tls sql -q "DROP DATABASE IF EXISTS $NAME; CALL DOLT_CLONE('--user', 'malte', 'https://dolt.cognovis.de/beads_$NAME');"

# Update metadata.json to point to the cloned DB name (beads_NAME)
python3 - "$NAME" <<'PYEOF'
import json, sys
path = '.beads/metadata.json'
d = json.load(open(path))
d = {k: v for k, v in d.items() if k in ('dolt_mode', 'dolt_database', 'project_id')}
d['dolt_database'] = 'beads_' + sys.argv[1]
json.dump(d, open(path, 'w'), indent=2)
PYEOF

bd dolt pull && bd dolt push --force
