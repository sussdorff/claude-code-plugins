#!/usr/bin/env bash
# wave-dispatch.sh — Set up cmux panes and dispatch cld -b for a wave
#
# Usage: wave-dispatch.sh <bead-id1> <bead-id2> ... [--workspace <id>] [--base-pane <id>]
#
# Creates one pane per bead (horizontal splits), names each surface,
# dispatches cld -b, and outputs the wave config JSON to stdout.
#
# The output JSON can be fed directly into wave-status.sh for monitoring.

set -euo pipefail

BEAD_IDS=()
WORKSPACE=""
BASE_PANE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace)
      WORKSPACE="$2"
      shift 2
      ;;
    --base-pane)
      BASE_PANE="$2"
      shift 2
      ;;
    *)
      BEAD_IDS+=("$1")
      shift
      ;;
  esac
done

if [[ ${#BEAD_IDS[@]} -eq 0 ]]; then
  echo "Error: no bead IDs provided" >&2
  echo "Usage: wave-dispatch.sh <bead-id1> <bead-id2> ... [--workspace <id>] [--base-pane <id>]" >&2
  exit 1
fi

# Helper: extract surface ID from cmux output like "OK surface:139 workspace:25"
extract_surface() {
  grep -o 'surface:[0-9]*' | head -1
}

# Determine workspace
if [[ -z "$WORKSPACE" ]]; then
  WORKSPACE=$(cmux identify --json 2>/dev/null | jq -r '.caller.workspace_ref // empty' 2>/dev/null || true)
  if [[ -z "$WORKSPACE" ]]; then
    echo "Error: could not determine workspace. Pass --workspace explicitly." >&2
    exit 1
  fi
fi

# Determine base pane for splits
if [[ -z "$BASE_PANE" ]]; then
  BASE_PANE=$(cmux identify --json 2>/dev/null | jq -r '.caller.pane_ref // empty' 2>/dev/null || true)
  if [[ -z "$BASE_PANE" ]]; then
    echo "Error: could not determine base pane. Pass --base-pane explicitly." >&2
    exit 1
  fi
fi

echo "Workspace: $WORKSPACE, Base pane: $BASE_PANE" >&2

DISPATCH_TIME=$(date -u +"%Y-%m-%dT%H:%M:%S")
BEADS_JSON="[]"

for i in "${!BEAD_IDS[@]}"; do
  BEAD_ID="${BEAD_IDS[$i]}"
  SHORT_ID=$(echo "$BEAD_ID" | sed 's/.*-//')

  # Always create a new split (never reuse the orchestrator's surface)
  SPLIT_OUTPUT=$(cmux new-split right --pane "$BASE_PANE" 2>&1 || true)
  SURFACE=$(echo "$SPLIT_OUTPUT" | extract_surface || true)

  if [[ -z "$SURFACE" ]]; then
    echo "Error: failed to create split for bead $BEAD_ID. Output: $SPLIT_OUTPUT" >&2
    continue
  fi

  # Wait for surface to be ready
  sleep 3

  # Rename the surface tab for observability
  cmux rename-tab --surface "$SURFACE" "${SHORT_ID}-impl" 2>/dev/null || true

  # Dispatch cld -b (the \n is interpreted by cmux as Enter)
  cmux send --surface "$SURFACE" "cld -b ${BEAD_ID}\n" 2>/dev/null || {
    echo "Warning: failed to send command to $SURFACE for bead $BEAD_ID" >&2
    continue
  }

  # Add to output JSON
  BEADS_JSON=$(echo "$BEADS_JSON" | jq \
    --arg id "$BEAD_ID" \
    --arg surface "$SURFACE" \
    '. + [{id: $id, surface: $surface}]')

  echo "Dispatched: $BEAD_ID → $SURFACE (${SHORT_ID}-impl)" >&2
done

# Output the wave config JSON (feed this to wave-status.sh)
jq -n \
  --arg dispatch_time "$DISPATCH_TIME" \
  --arg workspace "$WORKSPACE" \
  --argjson beads "$BEADS_JSON" \
  '{
    dispatch_time: $dispatch_time,
    workspace: $workspace,
    beads: $beads
  }'
