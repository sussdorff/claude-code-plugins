#!/usr/bin/env bash
# Switch hcloud 1Password plugin between Hetzner Cloud projects.
# Usage: switch-project.sh <default|shikigami>
# Project IDs:
#   Default:   xdxjwlnfkgjl2bnkwxq7rqf77u
#   Shikigami: tmtmfkzwjtrf57bjpp44qiwloq

set -euo pipefail

PROJECT="${1:-default}"
CONFIG="${HOME}/.config/op/plugins/hcloud.json"

case "${PROJECT,,}" in
  default)
    ITEM_ID="xdxjwlnfkgjl2bnkwxq7rqf77u"
    ;;
  shikigami)
    ITEM_ID="tmtmfkzwjtrf57bjpp44qiwloq"
    ;;
  *)
    echo "Usage: $0 <default|shikigami>" >&2
    exit 1
    ;;
esac

jq --arg id "$ITEM_ID" '.credentials[0].item_id = $id' "$CONFIG" > /tmp/hcloud.json \
  && mv /tmp/hcloud.json "$CONFIG"

echo "Switched to project: ${PROJECT}"
hcloud server list
