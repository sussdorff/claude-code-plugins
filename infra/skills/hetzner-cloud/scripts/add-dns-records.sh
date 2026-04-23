#!/usr/bin/env bash
# Add DNS records to a Hetzner zone.
# Usage: add-dns-records.sh <zone-id> <name> <type> <record> [<record> ...]
# Example: add-dns-records.sh 817812 @ MX "10 in1-smtp.messagingengine.com." "20 in2-smtp.messagingengine.com."
# Note: record names must be relative to the zone (e.g. @ not domain.de)

set -euo pipefail

ZONE_ID="${1:?zone-id required}"
NAME="${2:?name required}"
TYPE="${3:?type required}"
shift 3

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <zone-id> <name> <type> <record> [<record> ...]" >&2
  exit 1
fi

RECORD_ARGS=()
for rec in "$@"; do
  RECORD_ARGS+=(--record "$rec")
done

hcloud zone add-records "${RECORD_ARGS[@]}" --ttl 3600 "$ZONE_ID" "$NAME" "$TYPE"
