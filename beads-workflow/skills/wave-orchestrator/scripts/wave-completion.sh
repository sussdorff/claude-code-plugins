#!/usr/bin/env bash
# wave-completion.sh — Quick check if a wave is fully complete
#
# Usage: wave-completion.sh <wave-config.json>
#
# Checks both bead database status (bd show) and surface state.
# Returns JSON with completion status and any stragglers.
#
# Exit codes:
#   0 — all beads done
#   1 — wave not yet complete
#   2 — error

set -euo pipefail

CONFIG="$1"

if [[ ! -f "$CONFIG" ]]; then
  echo "Error: config file not found: $CONFIG" >&2
  exit 2
fi

BEAD_COUNT=$(jq '.beads | length' "$CONFIG")
ALL_CLOSED=true
ALL_IDLE=true
STRAGGLERS="[]"

for i in $(seq 0 $((BEAD_COUNT - 1))); do
  BEAD_ID=$(jq -r ".beads[$i].id" "$CONFIG")
  SURFACE=$(jq -r ".beads[$i].surface" "$CONFIG")

  # Check bd status
  BD_STATUS=$(bd show "$BEAD_ID" 2>/dev/null | grep -oE 'Status:\s+\S+' | sed 's/Status:\s*//' || echo "unknown")

  # Check surface state (quick — only last 5 lines)
  LAST_LINES=$(cmux read-screen --surface "$SURFACE" --lines 5 2>/dev/null || echo "UNREACHABLE")
  SURFACE_IDLE=false

  if echo "$LAST_LINES" | grep -qE '^\s*(\$|❯|➜|%)\s*$'; then
    SURFACE_IDLE=true
  fi
  if [[ "$LAST_LINES" == "UNREACHABLE" ]]; then
    # Surface gone — treat as done (process exited)
    SURFACE_IDLE=true
  fi

  if [[ "$BD_STATUS" != "closed" ]]; then
    ALL_CLOSED=false
    STRAGGLERS=$(echo "$STRAGGLERS" | jq \
      --arg id "$BEAD_ID" \
      --arg bd_status "$BD_STATUS" \
      --argjson surface_idle "$SURFACE_IDLE" \
      '. + [{id: $id, bd_status: $bd_status, surface_idle: $surface_idle}]')
  fi

  if [[ "$SURFACE_IDLE" != "true" ]]; then
    ALL_IDLE=false
  fi
done

# Check for follow-up beads that might have been created
# Scan all surfaces for "Created issue:" patterns
FOLLOW_UPS="[]"
for i in $(seq 0 $((BEAD_COUNT - 1))); do
  SURFACE=$(jq -r ".beads[$i].surface" "$CONFIG")
  SCREEN=$(cmux read-screen --surface "$SURFACE" --scrollback --lines 30 2>/dev/null || true)
  NEW_BEADS=$(echo "$SCREEN" | grep -oE 'Created issue: [a-zA-Z0-9_-]+' | sed 's/Created issue: //' || true)

  if [[ -n "$NEW_BEADS" ]]; then
    while IFS= read -r NEW_ID; do
      # Check if this follow-up bead is closed
      FU_STATUS=$(bd show "$NEW_ID" 2>/dev/null | grep -oE 'Status:\s+\S+' | sed 's/Status:\s*//' || echo "unknown")
      if [[ "$FU_STATUS" != "closed" ]]; then
        ALL_CLOSED=false
        FOLLOW_UPS=$(echo "$FOLLOW_UPS" | jq \
          --arg id "$NEW_ID" \
          --arg status "$FU_STATUS" \
          '. + [{id: $id, status: $status}]')
      fi
    done <<< "$NEW_BEADS"
  fi
done

COMPLETE=false
if [[ "$ALL_CLOSED" == "true" && "$ALL_IDLE" == "true" ]]; then
  COMPLETE=true
fi

jq -n \
  --argjson complete "$COMPLETE" \
  --argjson all_beads_closed "$ALL_CLOSED" \
  --argjson all_surfaces_idle "$ALL_IDLE" \
  --argjson stragglers "$STRAGGLERS" \
  --argjson follow_up_beads "$FOLLOW_UPS" \
  '{
    complete: $complete,
    all_beads_closed: $all_beads_closed,
    all_surfaces_idle: $all_surfaces_idle,
    stragglers: $stragglers,
    unclosed_follow_ups: $follow_up_beads
  }'

if [[ "$COMPLETE" == "true" ]]; then
  exit 0
else
  exit 1
fi
