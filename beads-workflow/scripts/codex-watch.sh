#!/usr/bin/env bash
# codex-watch.sh — Poll a Codex background job and emit structured events.
#
# Usage:
#   codex-watch.sh <jobId> <codex-companion-path> [worktree-dir]
#
# Emits one line per meaningful event to stdout:
#   PHASE_CHANGE        jobId=<id> phase=<phase>
#   STALL_DETECTED      jobId=<id> elapsed=<Xm>
#   CODEX_DONE          jobId=<id> elapsed=<Xs>
#   CODEX_FAILED        jobId=<id> elapsed=<Xs>
#   CODEX_CANCELLED     jobId=<id> elapsed=<Xs>
#   CODEX_WATCH_ERROR   jobId=<id> reason=<msg>   (repeated poll failures, not transient)
#   CODEX_WATCH_EXIT    jobId=<id>                (abnormal exit only — crash guard)
#
# Terminal events (DONE/FAILED/CANCELLED) are emitted and the script exits 0
# WITHOUT triggering CODEX_WATCH_EXIT.  CODEX_WATCH_EXIT fires ONLY on
# abnormal termination (crash, signal, unexpected errexit).
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
POLL_ERROR_MAX=5          # consecutive poll failures before CODEX_WATCH_ERROR

stall_count=0
last_phase=""
stall_emitted=false
poll_error_count=0
terminal_emitted=false    # set to true before any terminal exit

# EXIT trap — fires ONLY for abnormal exits (crash, signal).
# We clear it before normal terminal exits so it does not fire there.
_on_exit() {
    if [[ "$terminal_emitted" == "false" ]]; then
        echo "CODEX_WATCH_EXIT jobId=${JOB_ID}"
    fi
}
trap '_on_exit' EXIT

# --- JSON extraction helpers -------------------------------------------------

# Extract a string field from JSON using jq if available, else python3
json_field() {
    local json="$1"
    local field="$2"
    if command -v jq &>/dev/null; then
        printf '%s' "$json" | jq -r "$field // empty" 2>/dev/null || echo ""
    else
        python3 - "$json" "$field" 2>/dev/null <<'PYEOF' || echo ""
import json, sys
try:
    data = json.loads(sys.argv[1])
    keys = sys.argv[2].lstrip('.').split('.')
    val = data
    for k in keys:
        val = val.get(k, '') if isinstance(val, dict) else ''
    print(val or '')
except Exception:
    print('')
PYEOF
    fi
}

get_status() { json_field "$1" ".job.status"; }
get_phase()  { json_field "$1" ".job.phase"; }
get_elapsed(){ json_field "$1" ".job.elapsed"; }

# --- Poll loop ---------------------------------------------------------------

while true; do
    # Build status command
    CMD_ARGS=("$CODEX_COMPANION" status "$JOB_ID" --json)
    if [[ -n "$WORKTREE_DIR" ]]; then
        CMD_ARGS+=(--cwd "$WORKTREE_DIR")
    fi

    # Run status; collect stderr for error reporting
    POLL_STDERR_FILE=$(mktemp /tmp/codex-watch-err.XXXXXX)
    STATUS_OUTPUT=""
    POLL_OK=true
    STATUS_OUTPUT=$(node "${CMD_ARGS[@]}" 2>"$POLL_STDERR_FILE") || POLL_OK=false
    POLL_STDERR=$(cat "$POLL_STDERR_FILE" 2>/dev/null || true)
    rm -f "$POLL_STDERR_FILE"

    if [[ "$POLL_OK" == "false" ]]; then
        poll_error_count=$(( poll_error_count + 1 ))
        if [[ "$poll_error_count" -ge "$POLL_ERROR_MAX" ]]; then
            # Repeated failures — not transient. Emit error and exit.
            terminal_emitted=true
            REASON="${POLL_STDERR:-companion exited non-zero ${poll_error_count} times in a row}"
            # Truncate to one line for structured output
            REASON_ONELINE=$(echo "$REASON" | head -1 | tr -d '\n')
            echo "CODEX_WATCH_ERROR jobId=${JOB_ID} reason=${REASON_ONELINE}"
            exit 1
        fi
        # Transient: wait and retry
        sleep "$POLL_INTERVAL"
        continue
    fi

    # Successful poll — reset transient error counter
    poll_error_count=0

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

    # Terminal states — emit one event and exit cleanly (no CODEX_WATCH_EXIT)
    case "$STATUS" in
        completed)
            terminal_emitted=true
            echo "CODEX_DONE jobId=${JOB_ID} elapsed=${ELAPSED}"
            exit 0
            ;;
        failed)
            terminal_emitted=true
            echo "CODEX_FAILED jobId=${JOB_ID} elapsed=${ELAPSED}"
            exit 0
            ;;
        cancelled)
            terminal_emitted=true
            echo "CODEX_CANCELLED jobId=${JOB_ID} elapsed=${ELAPSED}"
            exit 0
            ;;
    esac

    # Stall detection: phase stuck in "starting" for > STALL_THRESHOLD cycles
    if [[ "$PHASE" == "$STALL_PHASE" ]]; then
        stall_count=$(( stall_count + 1 ))
        if [[ "$stall_count" -ge "$STALL_THRESHOLD" && "$stall_emitted" == "false" ]]; then
            stall_emitted=true
            elapsed_min=$(( STALL_THRESHOLD * POLL_INTERVAL / 60 ))
            echo "STALL_DETECTED jobId=${JOB_ID} elapsed=${elapsed_min}m"
            # Reset to allow a second stall cycle if the caller retries
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
