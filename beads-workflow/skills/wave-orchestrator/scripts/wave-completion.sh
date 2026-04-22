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
WAVE_ID=$(jq -r '.wave_id // "unknown"' "$CONFIG")
ALL_CLOSED=true
ALL_IDLE=true
STRAGGLERS="[]"
STALLS="[]"

# Stall detection thresholds
STALL_THRESHOLD_MIN=15
ACTIVE_WINDOW_MIN=5

# Compute elapsed minutes from dispatch time (used for stall detection)
DISPATCH_TIME=$(jq -r '.dispatch_time // empty' "$CONFIG")
if [[ -n "$DISPATCH_TIME" ]]; then
  DISPATCH_EPOCH=$(date -j -u -f "%Y-%m-%dT%H:%M:%S" "$DISPATCH_TIME" +%s 2>/dev/null \
    || date -u -d "${DISPATCH_TIME}Z" +%s 2>/dev/null \
    || echo "0")
  NOW_EPOCH=$(date -u +%s)
  ELAPSED_MIN=$(( (NOW_EPOCH - DISPATCH_EPOCH) / 60 ))
else
  ELAPSED_MIN=0
fi

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

  # Stall detection: surface idle + bd in_progress + elapsed >= threshold
  if [[ "$SURFACE_IDLE" == "true" && "$BD_STATUS" == "in_progress" && "$ELAPSED_MIN" -ge "$STALL_THRESHOLD_MIN" ]]; then
    IS_ACTIVE=false

    # Primary guard: query agent_calls for recent activity (agent_calls lives in ~/.claude/metrics.db, not in the Dolt beads DB)
    # Use epoch-second comparison to avoid text-sort mismatch between ISO-8601+TZ stored values
    # and SQLite's datetime() which produces bare "YYYY-MM-DD HH:MM:SS" strings.
    RECENT_CALLS=$(sqlite3 ~/.claude/metrics.db \
      "SELECT COUNT(*) FROM agent_calls WHERE bead_id='${BEAD_ID}' AND (strftime('%s','now') - strftime('%s', recorded_at)) < $((ACTIVE_WINDOW_MIN * 60))" \
      2>/dev/null || echo "0")
    if [[ "${RECENT_CALLS:-0}" =~ ^[1-9] ]]; then
      IS_ACTIVE=true
    fi

    # Fallback guard: check scrollback for recent tool-use markers
    if [[ "$IS_ACTIVE" == "false" ]]; then
      SCREEN_FULL=$(cmux read-screen --surface "$SURFACE" --scrollback --lines 100 2>&1 || true)
      if echo "$SCREEN_FULL" | grep -qE "invalid_params|not a terminal|Surface.*not found"; then
        SCREEN_FULL=""
      fi
      RECENT_TOOL_USE=$(echo "$SCREEN_FULL" | tail -30 | grep -cE '\bBash\b|\bRead\b|\bWrite\b|\bEdit\b|\bGrep\b|\bGlob\b|\bAgent\b|ToolUse|tool_use' || echo "0")
      if [[ "${RECENT_TOOL_USE:-0}" -gt 0 ]]; then
        IS_ACTIVE=true
      fi
    fi

    if [[ "$IS_ACTIVE" == "false" ]]; then
      STALL_TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
      echo "STALL: $BEAD_ID surface idle but bd status != closed (elapsed: ${ELAPSED_MIN}min)" >&2
      # Write diagnostic note to bead only once per wave run (idempotency guard).
      # Use a temp-file marker keyed to wave_id+bead_id — avoids parsing bd show output
      # (which includes the description, not just notes, making grep-based checks unreliable).
      STALL_MARKER="/tmp/wave-stall-${WAVE_ID}-${BEAD_ID}"
      if [[ ! -f "$STALL_MARKER" ]]; then
        touch "$STALL_MARKER"
        bd update "$BEAD_ID" --append-notes="STALL-DETECTED: wave-orchestrator observed surface idle + bd in_progress at ${STALL_TS}. Manual investigation required." 2>/dev/null || true
      fi
      # Track for JSON output
      STALLS=$(echo "${STALLS}" | jq \
        --arg id "$BEAD_ID" \
        --arg ts "$STALL_TS" \
        --argjson elapsed "$ELAPSED_MIN" \
        '. + [{id: $id, detected_at: $ts, elapsed_minutes: $elapsed}]')
    fi
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

# Metric-aggregation sanity check: bead_runs rows with this wave_id should equal BEAD_COUNT
METRICS_DB="${HOME}/.claude/metrics.db"
BEAD_RUNS_COUNT=0
METRICS_SANITY="skipped"
if [[ -f "$METRICS_DB" && "$WAVE_ID" != "unknown" ]]; then
  # Validate WAVE_ID is safe to interpolate into SQL (no single-quote injection)
  if [[ ! "$WAVE_ID" =~ ^[A-Za-z0-9_-]+$ ]]; then
    METRICS_SANITY="skipped: invalid wave_id"
  else
    SQLITE_STDERR=$(sqlite3 "$METRICS_DB" \
      "SELECT COUNT(*) FROM bead_runs WHERE wave_id = '${WAVE_ID}'" 2>&1 1>/dev/null || true)
    BEAD_RUNS_COUNT=$(sqlite3 "$METRICS_DB" \
      "SELECT COUNT(*) FROM bead_runs WHERE wave_id = '${WAVE_ID}'" 2>/dev/null || echo "")
    if [[ -n "$SQLITE_STDERR" ]]; then
      METRICS_SANITY="error: $(echo "$SQLITE_STDERR" | head -1)"
    elif [[ -z "$BEAD_RUNS_COUNT" ]]; then
      METRICS_SANITY="error: sqlite3 returned empty"
    elif [[ "$BEAD_RUNS_COUNT" -eq "$BEAD_COUNT" ]]; then
      METRICS_SANITY="ok"
    else
      METRICS_SANITY="mismatch: expected ${BEAD_COUNT} bead_runs rows, got ${BEAD_RUNS_COUNT}"
      echo "WARN: metrics sanity mismatch for wave ${WAVE_ID}: expected ${BEAD_COUNT} rows, got ${BEAD_RUNS_COUNT}" >&2
    fi
  fi
fi

jq -n \
  --argjson complete "$COMPLETE" \
  --argjson all_beads_closed "$ALL_CLOSED" \
  --argjson all_surfaces_idle "$ALL_IDLE" \
  --argjson stragglers "$STRAGGLERS" \
  --argjson follow_up_beads "$FOLLOW_UPS" \
  --argjson stalls "${STALLS}" \
  --arg metrics_sanity "$METRICS_SANITY" \
  --argjson bead_runs_count "${BEAD_RUNS_COUNT:-0}" \
  '{
    complete: $complete,
    all_beads_closed: $all_beads_closed,
    all_surfaces_idle: $all_surfaces_idle,
    stragglers: $stragglers,
    unclosed_follow_ups: $follow_up_beads,
    stalls: $stalls,
    metrics_sanity: $metrics_sanity,
    bead_runs_count: $bead_runs_count
  }'

if [[ "$COMPLETE" == "true" ]]; then
  exit 0
else
  exit 1
fi
