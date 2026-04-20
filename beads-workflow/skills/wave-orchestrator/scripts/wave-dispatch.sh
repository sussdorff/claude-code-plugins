#!/usr/bin/env bash
# wave-dispatch.sh — Set up cmux panes and dispatch cld -b for a wave
#
# Usage: wave-dispatch.sh <bead-id1> <bead-id2> ... [--workspace <id>] [--base-pane <id>]
#
# Creates ONE pane per bead (1-pane mode: full and quick-fix beads both use a single
# pane). Renames each surface, dispatches cld -b or cld -bq, and outputs wave config JSON.
# NOTE: cld -br (review-only sessions) is NOT used here. After CCP-2vo.4, bead-orchestrator
# runs all phases (including Codex review) inline in a single pane.
#
# The output JSON can be fed directly into wave-status.sh for monitoring.

set -euo pipefail

BEAD_IDS=()
QUICK_IDS=()
WORKSPACE=""
BASE_PANE=""
WAVE_ID=""

# Parse arguments
# Use --quick <id> to route specific beads to the quick-fix agent (cld -bq)
# All other IDs use the full bead-orchestrator (cld -b)
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
    --wave-id)
      WAVE_ID="$2"
      shift 2
      ;;
    --quick)
      QUICK_IDS+=("$2")
      shift 2
      ;;
    *)
      BEAD_IDS+=("$1")
      shift
      ;;
  esac
done

# Merge all IDs for validation (quick IDs are also dispatched, just with -bq)
ALL_IDS=("${BEAD_IDS[@]}" "${QUICK_IDS[@]}")

# Auto-generate wave_id if not provided
if [[ -z "$WAVE_ID" ]]; then
  WAVE_ID="wave-$(date -u +%Y%m%d-%H%M%S)"
fi

if [[ ${#ALL_IDS[@]} -eq 0 ]]; then
  echo "Error: no bead IDs provided" >&2
  echo "Usage: wave-dispatch.sh <bead-id1> ... [--quick <id>] ... [--workspace <id>] [--base-pane <id>]" >&2
  exit 1
fi

# Helper: check if a bead ID is in the quick-fix list
is_quick() {
  local id="$1"
  for qid in "${QUICK_IDS[@]}"; do
    [[ "$qid" == "$id" ]] && return 0
  done
  return 1
}

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

for i in "${!ALL_IDS[@]}"; do
  BEAD_ID="${ALL_IDS[$i]}"
  SHORT_ID=$(echo "$BEAD_ID" | sed 's/.*-//')

  # Determine dispatch mode
  # Both modes use a single pane — no paired review surface (1-pane mode per CCP-2vo.4)
  if is_quick "$BEAD_ID"; then
    CLD_FLAG="-bq"
    SURFACE_SUFFIX="qf"
  else
    CLD_FLAG="-b"
    SURFACE_SUFFIX="impl"  # no paired -impl/-review: Codex review runs inline
  fi

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
  cmux rename-tab --surface "$SURFACE" "${SHORT_ID}-${SURFACE_SUFFIX}" 2>/dev/null || true

  # Dispatch with appropriate cld flag (send text + explicit enter key)
  { cmux send --surface "$SURFACE" "WAVE_ID=${WAVE_ID} cld ${CLD_FLAG} ${BEAD_ID}" && cmux send-key --surface "$SURFACE" enter; } 2>/dev/null || {
    echo "Warning: failed to send command to $SURFACE for bead $BEAD_ID" >&2
    continue
  }

  # Add to output JSON (include mode for monitoring)
  BEADS_JSON=$(echo "$BEADS_JSON" | jq \
    --arg id "$BEAD_ID" \
    --arg surface "$SURFACE" \
    --arg mode "$(is_quick "$BEAD_ID" && echo "quick" || echo "full")" \
    '. + [{id: $id, surface: $surface, mode: $mode}]')

  echo "Dispatched ($CLD_FLAG): $BEAD_ID → $SURFACE (${SHORT_ID}-${SURFACE_SUFFIX})" >&2
done

# Output the wave config JSON (feed this to wave-status.sh)
jq -n \
  --arg dispatch_time "$DISPATCH_TIME" \
  --arg workspace "$WORKSPACE" \
  --arg wave_id "$WAVE_ID" \
  --argjson beads "$BEADS_JSON" \
  '{
    dispatch_time: $dispatch_time,
    workspace: $workspace,
    wave_id: $wave_id,
    beads: $beads
  }'
