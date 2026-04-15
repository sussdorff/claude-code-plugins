#!/usr/bin/env bash
# codex-watch.sh — Poll a Codex background job and emit structured events.
#
# Usage:
#   codex-watch.sh <jobId> <codex-companion-path> [worktree-dir]
#
# Emits one line per meaningful event to stdout:
#   PHASE_CHANGE     jobId=<id> phase=<phase>
#   STALL_DETECTED   jobId=<id> elapsed=<Xm>
#   CODEX_DONE       jobId=<id> elapsed=<Xs>
#   CODEX_FAILED     jobId=<id> elapsed=<Xs>
#   CODEX_CANCELLED  jobId=<id> elapsed=<Xs>
#   CODEX_WATCH_EXIT jobId=<id>   (always on exit — silence-on-crash impossible)
#
# Terminal states (DONE/FAILED/CANCELLED/STALL_DETECTED after 2nd stall) cause
# the script to exit with code 0.
#
# Field names verified against:
#   codex-companion.mjs lib/job-control.mjs + lib/tracked-jobs.mjs
#   job.status: queued | running | completed | failed | cancelled
#   job.phase:  queued | starting | reviewing | investigating | verifying |
#               editing | finalizing | done | failed | cancelled
#   job.elapsed: human-readable string from enrichJob() (e.g. "5m 30s")
#   status --json response shape: { "workspaceRoot": "...", "job": { ... } }

set -euo pipefail

JOB_ID="${1:?Usage: codex-watch.sh <jobId> <codex-companion> [worktree-dir]}"
CODEX_COMPANION="${2:?Missing codex-companion path}"
WORKTREE_DIR="${3:-}"

POLL_INTERVAL=10          # seconds between polls
STALL_PHASE="starting"    # phase that triggers stall detection
STALL_THRESHOLD=30        # poll cycles before STALL_DETECTED (30 * 10s = 5 min)

stall_count=0
last_phase=""
stall_emitted=false

# EXIT trap — always fires, ensures no silent exit
trap 'echo "CODEX_WATCH_EXIT jobId=${JOB_ID}"' EXIT

# --- JSON extraction helpers -------------------------------------------------

# Extract a string field from JSON using jq if available, else python3
json_field() {
    local json="$1"
    local field="$2"
    if command -v jq &>/dev/null; then
        echo "$json" | jq -r "$field // empty"
    else
        python3 -c "
import json, sys
try:
    data = json.loads('''${json}''')
    val = data
    for key in '${field}'.lstrip('.').split('.'):
        val = val.get(key, '')
    print(val or '')
except Exception:
    print('')
"
    fi
}

# Safe wrapper that returns empty string on parse failure
get_status() {
    local output="$1"
    json_field "$output" ".job.status" 2>/dev/null || echo ""
}

get_phase() {
    local output="$1"
    json_field "$output" ".job.phase" 2>/dev/null || echo ""
}

get_elapsed() {
    local output="$1"
    json_field "$output" ".job.elapsed" 2>/dev/null || echo "unknown"
}

# --- Poll loop ---------------------------------------------------------------

while true; do
    # Build status command
    CMD_ARGS=("$CODEX_COMPANION" status "$JOB_ID" --json)
    if [[ -n "$WORKTREE_DIR" ]]; then
        CMD_ARGS+=(--cwd "$WORKTREE_DIR")
    fi

    # Run status; tolerate transient failures (network blip, process restart)
    STATUS_OUTPUT=""
    if STATUS_OUTPUT=$(node "${CMD_ARGS[@]}" 2>/dev/null); then
        :
    else
        # Non-fatal: wait and retry
        sleep "$POLL_INTERVAL"
        continue
    fi

    STATUS=$(get_status "$STATUS_OUTPUT")
    PHASE=$(get_phase "$STATUS_OUTPUT")
    ELAPSED=$(get_elapsed "$STATUS_OUTPUT")

    # Guard: if status is empty the job record is not yet visible — wait
    if [[ -z "$STATUS" ]]; then
        sleep "$POLL_INTERVAL"
        continue
    fi

    # Emit phase changes (informational)
    if [[ -n "$PHASE" && "$PHASE" != "$last_phase" ]]; then
        if [[ -n "$last_phase" ]]; then
            echo "PHASE_CHANGE jobId=${JOB_ID} phase=${PHASE}"
        fi
        last_phase="$PHASE"
    fi

    # Terminal states — emit one line and exit (trap emits CODEX_WATCH_EXIT too,
    # but the caller should react to the terminal-state event, not the exit line)
    case "$STATUS" in
        completed)
            echo "CODEX_DONE jobId=${JOB_ID} elapsed=${ELAPSED}"
            exit 0
            ;;
        failed)
            echo "CODEX_FAILED jobId=${JOB_ID} elapsed=${ELAPSED}"
            exit 0
            ;;
        cancelled)
            echo "CODEX_CANCELLED jobId=${JOB_ID} elapsed=${ELAPSED}"
            exit 0
            ;;
    esac

    # Stall detection: phase stuck in "starting" for > STALL_THRESHOLD cycles
    if [[ "$PHASE" == "$STALL_PHASE" ]]; then
        stall_count=$(( stall_count + 1 ))
        if [[ "$stall_count" -ge "$STALL_THRESHOLD" && "$stall_emitted" == "false" ]]; then
            stall_emitted=true
            # Calculate elapsed minutes from cycles
            elapsed_min=$(( STALL_THRESHOLD * POLL_INTERVAL / 60 ))
            echo "STALL_DETECTED jobId=${JOB_ID} elapsed=${elapsed_min}m"
            # After emitting stall, keep polling — the caller decides to cancel+retry
            # If another STALL_THRESHOLD cycles pass, emit a second stall for 2nd stall path
            stall_count=0
            stall_emitted=false
        fi
    else
        # Phase moved on — reset stall counter
        stall_count=0
        stall_emitted=false
    fi

    sleep "$POLL_INTERVAL"
done
