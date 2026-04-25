#!/usr/bin/env bash
# phase-b-close-beads.sh - Phase B close-beads batch handler (Step 16b)
#
# Harvests 'Close reason:' from bead notes for all in-progress beads,
# closes them via bd close, ingests ccusage/Codex metrics, and syncs Dolt.
#
# This consolidates the ~6 bd list / bd show / bd close / metrics / dolt
# calls in session-close Step 16b into a single tool use.
#
# IMPORTANT: Requires that bead-orchestrator stamped 'Close reason:' into
# each bead's notes before session-close runs. If any in-progress bead has
# no close-reason note, the script returns a structured error listing which
# bead IDs need a reason — the caller composes reasons and reruns.
#
# Usage:
#   phase-b-close-beads.sh [--dry-run]
#
# Emits a single JSON document on stdout; stderr for human-readable progress.
#
# Exit codes:
#   0 - all beads closed (or no in-progress beads found)
#   3 - one or more beads have no close reason (partial JSON, missing_reason list)
#   1 - internal error
#
# Idempotency: safe to re-run. bd close on an already-closed bead is a no-op
# (bd prints a warning but exits 0). Dolt sync is always idempotent.
#
# Schema: phase-b-close-beads.schema.json

set -uo pipefail

# ---------------------------------------------------------------------------
# Flag parsing
# ---------------------------------------------------------------------------
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    *) shift ;;
  esac
done

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
if ! command -v bd &>/dev/null; then
  echo '{"error":"bd_not_found","closed":[],"close_failed":[],"missing_reason":[],"skipped_not_owned":[],"dolt_sync":{"status":"skipped","detail":"bd not found"},"metrics_ingest":{"status":"skipped","detail":"bd not found"}}' >&2
  exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"
PLUGIN_LIB="${CLAUDE_PLUGIN_ROOT:-${REPO_ROOT:-$HOME/code/claude-code-plugins}/beads-workflow}/lib/orchestrator"

# ---------------------------------------------------------------------------
# Result accumulators
# ---------------------------------------------------------------------------
CLOSED_BEADS=()        # JSON objects: {id, type, title, close_reason}
CLOSE_FAILED_BEADS=()  # JSON objects: {id, type, title, close_reason} — bd close failed
MISSING_REASON=()      # bead IDs that need a close reason
SKIPPED_NOT_OWNED=()   # bead IDs skipped because owned by a different session

# ---------------------------------------------------------------------------
# Find in-progress beads
# ---------------------------------------------------------------------------
echo "==> Finding in-progress beads" >&2

IN_PROGRESS_JSON=$(bd list --status=in_progress --json 2>/dev/null || echo "[]")
IN_PROGRESS_COUNT=$(echo "$IN_PROGRESS_JSON" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(len(d))" 2>/dev/null || echo "0")

echo "    found $IN_PROGRESS_COUNT in-progress bead(s)" >&2

if [[ "$IN_PROGRESS_COUNT" -eq 0 ]]; then
  echo '{"closed":[],"close_failed":[],"missing_reason":[],"skipped_not_owned":[],"dolt_sync":{"status":"skipped","detail":"no in-progress beads"},"metrics_ingest":{"status":"skipped","detail":"no beads to close"}}'
  exit 0
fi

# ---------------------------------------------------------------------------
# Process each in-progress bead
# ---------------------------------------------------------------------------
echo "==> Processing in-progress beads" >&2

# Extract IDs
BEAD_IDS=$(echo "$IN_PROGRESS_JSON" | python3 -c \
  "import sys,json; [print(b['id']) for b in json.load(sys.stdin)]" 2>/dev/null || echo "")

for bead_id in $BEAD_IDS; do
  echo "    checking $bead_id..." >&2

  # Get bead details
  BEAD_JSON=$(bd show "$bead_id" --json 2>/dev/null || echo "[]")
  BEAD_TITLE=$(echo "$BEAD_JSON" | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(d[0].get('title',''))" 2>/dev/null || echo "")
  BEAD_TYPE=$(echo "$BEAD_JSON" | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(d[0].get('type','task'))" 2>/dev/null || echo "task")
  BEAD_NOTES=$(echo "$BEAD_JSON" | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(d[0].get('notes',''))" 2>/dev/null || echo "")

  # Ownership check: if CCP_SESSION_ID is set, only close beads owned by this session
  BEAD_ASSIGNEE=$(echo "$BEAD_JSON" | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(d[0].get('assignee',''))" 2>/dev/null || echo "")
  CURRENT_SESSION="${CCP_SESSION_ID:-}"
  if [[ -n "$CURRENT_SESSION" && -n "$BEAD_ASSIGNEE" && "$BEAD_ASSIGNEE" != "$CURRENT_SESSION" ]]; then
    echo "    $bead_id: skipping — owned by '$BEAD_ASSIGNEE', not current session '$CURRENT_SESSION'" >&2
    SKIPPED_NOT_OWNED+=("$bead_id")
    continue
  fi

  # Extract 'Close reason:' from notes
  CLOSE_REASON=$(echo "$BEAD_NOTES" | grep -i '^Close reason:' | head -1 | sed 's/^[Cc]lose reason:[[:space:]]*//' || echo "")

  if [[ -z "$CLOSE_REASON" ]]; then
    echo "    $bead_id: missing close reason" >&2
    MISSING_REASON+=("$bead_id")
    continue
  fi

  echo "    $bead_id: close reason found — closing" >&2

  # Escape for JSON
  CLOSE_REASON_JSON=$(printf '%s' "$CLOSE_REASON" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")
  BEAD_TITLE_JSON=$(printf '%s' "$BEAD_TITLE" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")
  BEAD_TYPE_JSON=$(printf '%s' "$BEAD_TYPE" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")

  if [[ "$DRY_RUN" == "true" ]]; then
    echo "    [dry-run] would close $bead_id with reason: $CLOSE_REASON" >&2
    CLOSED_BEADS+=("{\"id\":$(printf '%s' "$bead_id" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))'),\"type\":$BEAD_TYPE_JSON,\"title\":$BEAD_TITLE_JSON,\"close_reason\":$CLOSE_REASON_JSON}")
  else
    if bd close "$bead_id" --reason="$CLOSE_REASON" 2>/dev/null; then
      echo "    $bead_id: closed" >&2
      CLOSED_BEADS+=("{\"id\":$(printf '%s' "$bead_id" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))'),\"type\":$BEAD_TYPE_JSON,\"title\":$BEAD_TITLE_JSON,\"close_reason\":$CLOSE_REASON_JSON}")
    else
      echo "    $bead_id: bd close failed" >&2
      CLOSE_FAILED_BEADS+=("{\"id\":$(printf '%s' "$bead_id" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))'),\"type\":$BEAD_TYPE_JSON,\"title\":$BEAD_TITLE_JSON,\"close_reason\":$CLOSE_REASON_JSON}")
    fi
  fi
done

# ---------------------------------------------------------------------------
# Check for missing reasons — return early if any
# ---------------------------------------------------------------------------
if [[ "${#MISSING_REASON[@]}" -gt 0 ]]; then
  echo "==> Missing close reasons for ${#MISSING_REASON[@]} bead(s) — returning exit 3" >&2

  MISSING_JSON=$(printf '%s\n' "${MISSING_REASON[@]}" | jq -R . | jq -s .)
  CLOSED_JSON="[]"
  if [[ "${#CLOSED_BEADS[@]}" -gt 0 ]]; then
    CLOSED_JSON="[$(IFS=','; echo "${CLOSED_BEADS[*]}")]"
  fi
  CLOSE_FAILED_JSON="[]"
  if [[ "${#CLOSE_FAILED_BEADS[@]}" -gt 0 ]]; then
    CLOSE_FAILED_JSON="[$(IFS=','; echo "${CLOSE_FAILED_BEADS[*]}")]"
  fi
  SKIPPED_NOT_OWNED_JSON="[]"
  if [[ "${#SKIPPED_NOT_OWNED[@]}" -gt 0 ]]; then
    SKIPPED_NOT_OWNED_JSON=$(printf '%s\n' "${SKIPPED_NOT_OWNED[@]}" | jq -R . | jq -s .)
  fi

  jq -cn \
    --argjson closed "$CLOSED_JSON" \
    --argjson close_failed "$CLOSE_FAILED_JSON" \
    --argjson missing "$MISSING_JSON" \
    --argjson skipped_not_owned "$SKIPPED_NOT_OWNED_JSON" \
    '{
      closed: $closed,
      close_failed: $close_failed,
      missing_reason: $missing,
      skipped_not_owned: $skipped_not_owned,
      dolt_sync: {status: "skipped", detail: "missing close reasons — sync deferred"},
      metrics_ingest: {status: "skipped", detail: "missing close reasons — ingest deferred"}
    }'
  exit 3
fi

# ---------------------------------------------------------------------------
# Metrics ingest (non-blocking)
# ---------------------------------------------------------------------------
echo "==> Metrics ingest" >&2

METRICS_STATUS="skipped"
METRICS_DETAIL="no plugin lib"

if [[ -d "$PLUGIN_LIB" && "$DRY_RUN" == "false" ]]; then
  SINCE=$(date -v-7d +%Y%m%d 2>/dev/null || date -d '-7 days' +%Y%m%d 2>/dev/null || date -d '7 days ago' +%Y%m%d 2>/dev/null || echo "")
  if [[ -z "$SINCE" ]]; then
    METRICS_STATUS="skipped"
    METRICS_DETAIL="cannot compute date range"
    echo "    skipped metrics ingest: cannot compute date range" >&2
  else
    INGEST_ERRORS=0

    for bead_json in "${CLOSED_BEADS[@]+"${CLOSED_BEADS[@]}"}"; do
      bead_id=$(echo "$bead_json" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['id'])" 2>/dev/null || echo "")
      [[ -z "$bead_id" ]] && continue

      python3 "$PLUGIN_LIB/ingest_ccusage.py" --bead "$bead_id" --since "$SINCE" 2>/dev/null || \
        { echo "    ccusage ingest failed for $bead_id (non-blocking)" >&2; (( INGEST_ERRORS++ )) || true; }
      python3 "$PLUGIN_LIB/ingest_codex.py" --bead "$bead_id" --since "$SINCE" 2>/dev/null || \
        { echo "    codex ingest failed for $bead_id (non-blocking)" >&2; (( INGEST_ERRORS++ )) || true; }
    done

    if [[ "$INGEST_ERRORS" -eq 0 ]]; then
      METRICS_STATUS="ok"
      METRICS_DETAIL="${#CLOSED_BEADS[@]} bead(s) ingested"
    else
      METRICS_STATUS="partial"
      METRICS_DETAIL="$INGEST_ERRORS ingest error(s) (non-blocking)"
    fi
  fi
elif [[ "$DRY_RUN" == "true" ]]; then
  METRICS_STATUS="skipped"
  METRICS_DETAIL="dry-run"
fi
echo "    metrics status: $METRICS_STATUS" >&2

# ---------------------------------------------------------------------------
# Dolt sync
# ---------------------------------------------------------------------------
echo "==> Dolt sync" >&2

DOLT_STATUS="skipped"
DOLT_DETAIL=""

if [[ "$DRY_RUN" == "true" ]]; then
  DOLT_STATUS="skipped"
  DOLT_DETAIL="dry-run"
  echo "    skipped (dry-run)" >&2
else
  DOLT_OUT=$(bd dolt commit 2>&1 && bd dolt pull 2>&1 && bd dolt push --force 2>&1) || DOLT_EXIT=$?
  DOLT_EXIT=${DOLT_EXIT:-0}
  if [[ "$DOLT_EXIT" -eq 0 ]]; then
    DOLT_STATUS="ok"
    DOLT_DETAIL="committed, pulled, pushed"
    echo "    dolt sync ok" >&2
  else
    DOLT_STATUS="failed"
    DOLT_DETAIL="exit $DOLT_EXIT — $DOLT_OUT"
    echo "    dolt sync failed (non-blocking): $DOLT_OUT" >&2
  fi
fi


# ---------------------------------------------------------------------------
# Lock: release session-close lock
# ---------------------------------------------------------------------------
# Release after all bead operations are done (close + dolt sync).
# This unblocks the next session-close waiting in the queue.
REPO_ROOT_FOR_LOCK="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"
if [[ -n "$REPO_ROOT_FOR_LOCK" ]]; then
  HANDLERS_DIR_FOR_LOCK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  LOCK_FILE_RELEASE="${REPO_ROOT_FOR_LOCK}/.session-close.lock"
  bash "$HANDLERS_DIR_FOR_LOCK/session-close-lock.sh" release "$LOCK_FILE_RELEASE" || true
fi

# ---------------------------------------------------------------------------
# Emit JSON
# ---------------------------------------------------------------------------
echo "==> Emitting JSON result" >&2

CLOSED_JSON="[]"
if [[ "${#CLOSED_BEADS[@]}" -gt 0 ]]; then
  CLOSED_JSON="[$(IFS=','; echo "${CLOSED_BEADS[*]}")]"
fi

CLOSE_FAILED_JSON="[]"
if [[ "${#CLOSE_FAILED_BEADS[@]}" -gt 0 ]]; then
  CLOSE_FAILED_JSON="[$(IFS=','; echo "${CLOSE_FAILED_BEADS[*]}")]"
fi

MISSING_JSON="[]"
# (MISSING_REASON is empty here — we returned early above if non-empty)

SKIPPED_NOT_OWNED_FINAL_JSON="[]"
if [[ "${#SKIPPED_NOT_OWNED[@]}" -gt 0 ]]; then
  SKIPPED_NOT_OWNED_FINAL_JSON=$(printf '%s\n' "${SKIPPED_NOT_OWNED[@]}" | jq -R . | jq -s .)
fi

jq -cn \
  --argjson closed "$CLOSED_JSON" \
  --argjson close_failed "$CLOSE_FAILED_JSON" \
  --argjson missing "$MISSING_JSON" \
  --argjson skipped_not_owned "$SKIPPED_NOT_OWNED_FINAL_JSON" \
  --arg ds "$DOLT_STATUS" --arg dd "$DOLT_DETAIL" \
  --arg ms "$METRICS_STATUS" --arg md "$METRICS_DETAIL" \
  '{
    closed: $closed,
    close_failed: $close_failed,
    missing_reason: $missing,
    skipped_not_owned: $skipped_not_owned,
    dolt_sync: {status: $ds, detail: $dd},
    metrics_ingest: {status: $ms, detail: $md}
  }'
