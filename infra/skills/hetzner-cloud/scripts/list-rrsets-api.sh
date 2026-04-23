#!/usr/bin/env bash
# List or delete DNS RRSets via the Hetzner DNS API directly.
# Fallback for operations not supported by hcloud zone subcommands.
# Usage: list-rrsets-api.sh <zone-id> [delete <name> <type>]

set -euo pipefail

ZONE_ID="${1:?zone-id required}"
ACTION="${2:-list}"
HCLOUD_TOKEN=$(op item get xdxjwlnfkgjl2bnkwxq7rqf77u --vault "API Keys" --fields token --reveal)

case "$ACTION" in
  list)
    curl -s -H "Authorization: Bearer ${HCLOUD_TOKEN}" \
      "https://api.hetzner.cloud/v1/zones/${ZONE_ID}/rrsets?per_page=100" \
      | jq '.rrsets[] | "\(.name) \(.type) \([.records[].value] | join(", "))"' -r
    ;;
  delete)
    NAME="${3:?name required for delete}"
    TYPE="${4:?type required for delete}"
    curl -s -X DELETE -H "Authorization: Bearer ${HCLOUD_TOKEN}" \
      "https://api.hetzner.cloud/v1/zones/${ZONE_ID}/rrsets/${NAME}/${TYPE}"
    ;;
  *)
    echo "Usage: $0 <zone-id> [list|delete <name> <type>]" >&2
    exit 1
    ;;
esac
