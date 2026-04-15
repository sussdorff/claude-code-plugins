#!/usr/bin/env bash
# wave-status.sh — Single-call monitoring for all beads in a wave
#
# Usage: wave-status.sh <wave-config.json>
#
# Input: JSON file with wave configuration:
#   {
#     "dispatch_time": "2026-03-30T14:00:00",
#     "beads": [
#       {"id": "mira-0al", "surface": "surface:3"},
#       {"id": "mira-doq", "surface": "surface:5"}
#     ]
#   }
#
# Output: JSON status report to stdout
#
# The script reads all surfaces in parallel, pattern-matches known status
# indicators, cross-checks against bd show, and detects follow-up beads.

set -euo pipefail

CONFIG="$1"

if [[ ! -f "$CONFIG" ]]; then
  echo "Error: config file not found: $CONFIG" >&2
  exit 1
fi

# Parse dispatch time and compute elapsed minutes
DISPATCH_TIME=$(jq -r '.dispatch_time' "$CONFIG")
if [[ "$DISPATCH_TIME" != "null" && -n "$DISPATCH_TIME" ]]; then
  DISPATCH_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%S" "$DISPATCH_TIME" +%s 2>/dev/null || echo "0")
  NOW_EPOCH=$(date +%s)
  if [[ "$DISPATCH_EPOCH" -gt 0 ]]; then
    ELAPSED_MIN=$(( (NOW_EPOCH - DISPATCH_EPOCH) / 60 ))
  else
    ELAPSED_MIN=-1
  fi
else
  ELAPSED_MIN=-1
fi

BEAD_COUNT=$(jq '.beads | length' "$CONFIG")
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

# Read all surfaces in parallel
for i in $(seq 0 $((BEAD_COUNT - 1))); do
  BEAD_ID=$(jq -r ".beads[$i].id" "$CONFIG")
  SURFACE=$(jq -r ".beads[$i].surface" "$CONFIG")

  (
    # The parallel subshell inherits `set -euo pipefail` — if cmux read-screen
    # exits non-zero (dead pane), the subshell would die before writing its
    # result file. `|| true` preserves output (via 2>&1) while forcing exit 0.
    SCREEN=$(cmux read-screen --surface "$SURFACE" --scrollback --lines 60 2>&1 || true)

    # Determine status from screen content
    STATUS="unknown"
    DETAIL=""

    # Pane-liveness check — a surface that no longer hosts a terminal returns
    # "Error: invalid_params: Surface is not a terminal" (or similar). This is
    # distinct from a live pane at idle: live panes return their current buffer
    # content. Without this check, the status script treats a dead pane's
    # leftover scrollback as if it were live, producing false "in_progress" or
    # "session_close" readings.
    if echo "$SCREEN" | grep -qE "invalid_params|not a terminal|Surface.*not found|no such surface"; then
      STATUS="dead"
      DETAIL="Surface terminated (pane closed)"
      SCREEN=""   # discard error output so downstream greps don't match on it
    elif echo "$SCREEN" | grep -q "BLOCKED: Missing Scenario"; then
      STATUS="blocked"
      DETAIL="Missing scenario section"
    elif echo "$SCREEN" | grep -qiE "error|panic|fatal|traceback|ENOENT|ECONNREFUSED"; then
      # Check if it's a real error (not just test output showing error handling)
      if echo "$SCREEN" | tail -5 | grep -qiE "error|panic|fatal|traceback"; then
        STATUS="failed"
        DETAIL=$(echo "$SCREEN" | grep -iE "error|panic|fatal|traceback" | tail -1 | head -c 120)
      fi
    fi

    # Override with more specific patterns (order matters — later wins)
    if echo "$SCREEN" | grep -q "Handoff to Session Close"; then
      STATUS="session_close"
      DETAIL="Implementation done, session close running"
    fi
    if echo "$SCREEN" | grep -q "review-agent\|cmux-reviewer\|Review iteration"; then
      STATUS="in_review"
      # Try to extract iteration number
      ITER=$(echo "$SCREEN" | grep -oE "iteration [0-9]+/[0-9]+" | tail -1)
      DETAIL="Review active${ITER:+ ($ITER)}"
    fi
    if echo "$SCREEN" | grep -q "session-close"; then
      STATUS="session_close"
      DETAIL="Session close in progress"
    fi
    if echo "$SCREEN" | grep -qiE "PIPELINE FAILED|pipeline.*failed|CI pipeline.*fail"; then
      STATUS="pipeline_failed"
      DETAIL=$(echo "$SCREEN" | grep -iE "PIPELINE FAILED|pipeline.*failed|CI pipeline.*fail" | tail -1 | head -c 120)
    fi
    # Check for active editing/testing (generic in-progress)
    if [[ "$STATUS" == "unknown" ]]; then
      if echo "$SCREEN" | grep -qE "pytest|jest|vitest|bun test|Running tests|PASS|FAIL"; then
        STATUS="in_progress"
        DETAIL="Running tests"
      elif echo "$SCREEN" | grep -qE "Edit|Write|Bash|Read|Grep"; then
        STATUS="in_progress"
        DETAIL="Active editing"
      fi
    fi

    # Check for idle shell (done) — empty prompt, no Claude session
    # Look at the last few lines for a bare prompt
    LAST_LINES=$(echo "$SCREEN" | tail -3)
    if echo "$LAST_LINES" | grep -qE '^\s*(\$|❯|➜|%)\s*$'; then
      # Bare prompt with nothing after it — likely done
      STATUS="done"
      DETAIL="Shell idle, no active session"
    fi

    # Detect follow-up beads (bd create in scrollback)
    FOLLOW_UPS=$(echo "$SCREEN" | grep -oE 'Created issue: [a-zA-Z0-9_-]+' | sed 's/Created issue: //' || true)

    # Get bd status — matches [● P2 · CLOSED] / IN_PROGRESS / OPEN / BLOCKED
    BD_STATUS=$(bd show "$BEAD_ID" 2>/dev/null | grep -oE '\b(OPEN|CLOSED|IN_PROGRESS|BLOCKED)\b' | head -1 | tr '[:upper:]' '[:lower:]' || echo "unknown")

    # If bd says closed, trust that over screen reading
    if [[ "$BD_STATUS" == "closed" ]]; then
      STATUS="done"
      DETAIL="Bead closed in database"
    fi

    # Write result
    jq -n \
      --arg id "$BEAD_ID" \
      --arg surface "$SURFACE" \
      --arg status "$STATUS" \
      --arg detail "$DETAIL" \
      --arg bd_status "$BD_STATUS" \
      --arg follow_ups "$FOLLOW_UPS" \
      '{id: $id, surface: $surface, status: $status, detail: $detail, bd_status: $bd_status, follow_up_beads: ($follow_ups | split("\n") | map(select(length > 0)))}' \
      > "$TMPDIR/bead-$i.json"
  ) &
done

# Wait for all parallel reads
wait

# Assemble results
ALL_DONE=true
BEADS_JSON="["
FOLLOW_UPS_ALL="[]"

for i in $(seq 0 $((BEAD_COUNT - 1))); do
  RESULT="$TMPDIR/bead-$i.json"
  if [[ -f "$RESULT" ]]; then
    BEAD_JSON=$(cat "$RESULT")
    BEAD_STATUS=$(echo "$BEAD_JSON" | jq -r '.status')

    if [[ "$BEAD_STATUS" != "done" ]]; then
      ALL_DONE=false
    fi
    # pipeline_failed is never "done" — requires fix agent
    if [[ "$BEAD_STATUS" == "pipeline_failed" ]]; then
      ALL_DONE=false
    fi

    # Collect follow-up beads
    BEAD_FOLLOW_UPS=$(echo "$BEAD_JSON" | jq '.follow_up_beads')
    FOLLOW_UPS_ALL=$(echo "$FOLLOW_UPS_ALL" "$BEAD_FOLLOW_UPS" | jq -s 'add | unique')

    if [[ $i -gt 0 ]]; then
      BEADS_JSON+=","
    fi
    BEADS_JSON+="$BEAD_JSON"
  fi
done
BEADS_JSON+="]"

# Build final output
jq -n \
  --argjson elapsed "$ELAPSED_MIN" \
  --argjson beads "$BEADS_JSON" \
  --argjson all_done "$ALL_DONE" \
  --argjson follow_up_beads "$FOLLOW_UPS_ALL" \
  '{
    elapsed_minutes: $elapsed,
    beads: $beads,
    all_done: $all_done,
    follow_up_beads: $follow_up_beads
  }'
