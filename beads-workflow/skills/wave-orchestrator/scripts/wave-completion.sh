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

  # Check bd status. `bd show` prints the status in a bracketed header like
  # `[● P1 · CLOSED]`, not as a `Status:` line — match that pattern.
  BD_STATUS=$(bd show "$BEAD_ID" 2>/dev/null | grep -oE '\b(OPEN|CLOSED|IN_PROGRESS|BLOCKED)\b' | head -1 | tr '[:upper:]' '[:lower:]')
  BD_STATUS="${BD_STATUS:-unknown}"

  # Check surface state (quick — only last 5 lines). Capture stdout+stderr
  # with `|| true` so set -e doesn't kill us when a pane is dead.
  LAST_LINES=$(cmux read-screen --surface "$SURFACE" --lines 5 2>&1 || true)
  SURFACE_IDLE=false

  if echo "$LAST_LINES" | grep -qE "invalid_params|not a terminal|Surface.*not found|no such surface"; then
    # Surface gone — treat as idle (process exited). The bd status check above
    # is the authoritative completion signal; this is only about liveness.
    SURFACE_IDLE=true
  elif echo "$LAST_LINES" | grep -qE '^\s*(\$|❯|➜|%)\s*$'; then
    # Only idle if no active thinking markers are present — Claude Code shows
    # a bare prompt on the bottom line even while actively thinking (e.g.
    # "Newspapering... 12m 2s" with ❯ still visible below it).
    if ! echo "$LAST_LINES" | grep -qE 'Newspapering|Baking|Crunched|Churned|Thinking|[0-9]+m\s*[0-9]+s|[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]'; then
      SURFACE_IDLE=true
    fi
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
  SCREEN=$(cmux read-screen --surface "$SURFACE" --scrollback --lines 30 2>&1 || true)
  # Skip dead surfaces — their "output" is an error message, not scrollback
  if echo "$SCREEN" | grep -qE "invalid_params|not a terminal|Surface.*not found|no such surface"; then
    SCREEN=""
  fi
  NEW_BEADS=$(echo "$SCREEN" | grep -oE 'Created issue: [a-zA-Z0-9_-]+' | sed 's/Created issue: //' || true)

  if [[ -n "$NEW_BEADS" ]]; then
    while IFS= read -r NEW_ID; do
      # Check if this follow-up bead is closed
      FU_STATUS=$(bd show "$NEW_ID" 2>/dev/null | grep -oE '\b(OPEN|CLOSED|IN_PROGRESS|BLOCKED)\b' | head -1 | tr '[:upper:]' '[:lower:]')
      FU_STATUS="${FU_STATUS:-unknown}"
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
