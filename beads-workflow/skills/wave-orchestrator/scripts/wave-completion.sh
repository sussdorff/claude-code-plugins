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

# Position-based idle check: last non-empty line must be the prompt,
# and the line immediately before it must NOT be an active-thinking marker.
_surface_is_idle() {
  local lines="$1"
  # Find the last non-empty line
  local last_nonempty
  last_nonempty=$(echo "$lines" | grep -v '^\s*$' | tail -1)
  # Must end with a bare prompt
  if ! echo "$last_nonempty" | grep -qE '^\s*(\$|❯|➜|%)\s*$'; then
    return 1  # not idle — no prompt on last non-empty line
  fi
  # Check the 2 non-empty lines immediately preceding the prompt.
  # Using 2 lines (not 1) covers cases where Claude renders an extra status
  # line (e.g. "Press Ctrl+C to interrupt") between the thinking indicator
  # and the prompt row.
  local preceding_lines
  preceding_lines=$(echo "$lines" | grep -v '^\s*$' | tail -3 | head -2)
  # If any preceding line is an active-thinking marker, not idle
  if echo "$preceding_lines" | grep -qE 'Newspapering|Baking|Crunched|Churned|Thinking|[0-9]+m\s*[0-9]+s|[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]'; then
    return 1  # not idle — active thinking visible adjacent to prompt
  fi
  return 0  # idle — prompt is last, no active thinking immediately before it
}

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
  elif _surface_is_idle "$LAST_LINES"; then
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
