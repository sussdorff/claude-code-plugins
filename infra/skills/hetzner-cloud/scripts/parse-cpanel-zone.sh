#!/usr/bin/env bash
# Parse DNS zone records from cPanel (Serverprofis) — records are base64-encoded.
# Usage: parse-cpanel-zone.sh <domain>
# Requires: op (1Password CLI), python3

set -euo pipefail

DOMAIN="${1:?domain required}"
SP_TOKEN=$(op read "op://API Keys/SP-Server/Token")

curl -sk -H "Authorization: cpanel erpproje:${SP_TOKEN}" \
  "https://cp220.sp-server.net:2083/execute/DNS/parse_zone?zone=${DOMAIN}" \
  | python3 - <<'PYEOF'
import json, sys, base64
data = json.load(sys.stdin)
for r in data["data"]:
    if r["type"] != "record": continue
    name = base64.b64decode(r["dname_b64"]).decode()
    rtype = r["record_type"]
    vals = [base64.b64decode(v).decode() for v in r.get("data_b64", [])]
    if rtype == "SOA": continue
    print(f"{name:40s} {r.get('ttl', '-'):>6} {rtype:6s} {' '.join(vals)}")
PYEOF
