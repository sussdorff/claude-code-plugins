#!/usr/bin/env bash
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
