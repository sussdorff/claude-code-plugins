#!/usr/bin/env bash
# wave-dispatch.sh — Set up cmux panes and dispatch cld -b for a wave
#
# Usage: wave-dispatch.sh <bead-id1> <bead-id2> ... [--workspace <id>] [--base-pane <id>]
#
# Creates ONE pane per bead (1-pane mode: full and quick-fix beads both use a single
# pane). Renames each surface, dispatches cld -b or cld -bq, and outputs wave config JSON.
# Both modes run all phases (including Codex adversarial review) inline — the old
# 2-pane review flow was removed in CCP-2vo.10.
#
# The output JSON can be fed directly into wave-status.sh for monitoring.

set -euo pipefail

BEAD_IDS=()
QUICK_IDS=()
WORKSPACE=""
BASE_SURFACE=""
WAVE_ID=""
SKIP_SCENARIOS=0

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
      BASE_SURFACE="$2"
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
    --skip-scenarios)
      SKIP_SCENARIOS=1
      shift
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
  echo "Usage: wave-dispatch.sh <bead-id1> ... [--quick <id>] ... [--workspace <id>] [--base-pane <id>] [--skip-scenarios]" >&2
  exit 1
fi

# Scenario gate: feature beads must have a ## Scenario section before dispatch.
# Runs BEFORE any pane is created so no surfaces are wasted on blocked beads.
if [[ "$SKIP_SCENARIOS" -eq 0 ]]; then
  MISSING_SCENARIOS=()
  for id in "${ALL_IDS[@]}"; do
    BEAD_TYPE=$(bd show "$id" --json 2>/dev/null | jq -r '.type // ""' 2>/dev/null || true)
    if [[ "$BEAD_TYPE" == "feature" ]]; then
      if ! bd show "$id" 2>/dev/null | grep -qE "^## (Scenario|Szenario)"; then
        MISSING_SCENARIOS+=("$id")
      fi
    fi
  done
  if [[ ${#MISSING_SCENARIOS[@]} -gt 0 ]]; then
    echo "Error: the following feature bead(s) are missing a ## Scenario section:" >&2
    for id in "${MISSING_SCENARIOS[@]}"; do
      echo "  - $id" >&2
    done
    echo "" >&2
    echo "Run the scenario generator for each bead, then retry:" >&2
    echo "  Agent(subagent_type='dev-tools:scenario-generator', prompt='Generate scenarios for ${MISSING_SCENARIOS[*]}')" >&2
    echo "" >&2
    echo "To bypass this check (not recommended): add --skip-scenarios" >&2
    exit 1
  fi
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

# Determine base surface for splits
# new-split needs a surface ref (surface:N), not a pane ref (pane:N)
if [[ -z "$BASE_SURFACE" ]]; then
  BASE_SURFACE=$(cmux identify --json 2>/dev/null | jq -r '.caller.surface_ref // empty' 2>/dev/null || true)
  if [[ -z "$BASE_SURFACE" ]]; then
    echo "Error: could not determine base surface. Pass --base-pane explicitly." >&2
    exit 1
  fi
fi

echo "Workspace: $WORKSPACE, Base surface: $BASE_SURFACE" >&2

# Pre-dispatch filter: skip beads that are already in_progress or closed.
# Runs BEFORE any pane is created so no surfaces are wasted on active beads.
DISPATCHABLE=()
SKIPPED_JSON="[]"
for id in "${ALL_IDS[@]}"; do
  _BEAD_STATUS=$(bd show "$id" --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0].get('status',''))" 2>/dev/null || echo "open")
  if [[ "$_BEAD_STATUS" == "in_progress" || "$_BEAD_STATUS" == "closed" ]]; then
    echo "Skipping $id (status=$_BEAD_STATUS)" >&2
    SKIPPED_JSON=$(echo "$SKIPPED_JSON" | jq --arg id "$id" --arg status "$_BEAD_STATUS" \
      '. + [{id: $id, status: $status, reason: "already_active"}]')
  else
    DISPATCHABLE+=("$id")
  fi
done

# Rebuild filtered ID arrays to only include dispatchable beads
BEAD_IDS_FILTERED=()
QUICK_IDS_FILTERED=()
for id in "${BEAD_IDS[@]}"; do
  for d in "${DISPATCHABLE[@]}"; do
    [[ "$id" == "$d" ]] && BEAD_IDS_FILTERED+=("$id") && break
  done
done
for id in "${QUICK_IDS[@]}"; do
  for d in "${DISPATCHABLE[@]}"; do
    [[ "$id" == "$d" ]] && QUICK_IDS_FILTERED+=("$id") && break
  done
done
BEAD_IDS=("${BEAD_IDS_FILTERED[@]}")
QUICK_IDS=("${QUICK_IDS_FILTERED[@]}")
ALL_IDS=("${DISPATCHABLE[@]}")

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
  # --surface takes a surface ref (surface:N); --pane is not a valid flag for new-split
  SPLIT_OUTPUT=$(cmux new-split right --surface "$BASE_SURFACE" --workspace "$WORKSPACE" 2>&1 || true)
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
  --argjson skipped "$SKIPPED_JSON" \
  '{
    dispatch_time: $dispatch_time,
    workspace: $workspace,
    wave_id: $wave_id,
    beads: $beads,
    skipped: $skipped
  }'
