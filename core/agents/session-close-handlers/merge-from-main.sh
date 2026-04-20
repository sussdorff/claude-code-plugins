#!/usr/bin/env bash
# merge-from-main.sh - fetch origin/main and merge it into the current branch
#
# Usage: merge-from-main.sh [--dry-run] [--label <text>]
#
# Called by session-close Step 1 (first merge) and Step 14 (second merge).
# The double-merge strategy requires this to run twice around the ship-close
# work to shrink the race window for parallel session-closes.
#
# Behaviour:
#   - Skip cleanly when the current branch is "main" (we can't merge main into
#     main; Step 1/14 only run in worktrees).
#   - In --dry-run, report what would happen without fetching or merging.
#   - On successful merge, exit 0.
#   - On merge conflict, exit 2 — caller MUST stop session-close and surface
#     the conflict so the user can resolve it.
#
# Output (stdout, KV lines):
#   MERGE_FROM_MAIN_STATUS=success|skipped_on_main|skipped_dry_run|conflict|error_fetch
#   MERGE_FROM_MAIN_LABEL=<label>     (echoed back when --label is set)
#
# Exit codes:
#   0 - success or a non-error skip (on_main, dry_run)
#   1 - transient error (e.g. fetch failed) — caller should warn, may retry
#   2 - merge conflict — caller MUST stop

set -uo pipefail

DRY_RUN=false
LABEL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --label) LABEL="${2:-}"; shift 2 ;;
    *) shift ;;
  esac
done

emit_status() {
  echo "MERGE_FROM_MAIN_STATUS=$1"
  [[ -n "$LABEL" ]] && echo "MERGE_FROM_MAIN_LABEL=$LABEL"
}

BRANCH="$(git branch --show-current 2>/dev/null || echo "")"

if [[ -z "$BRANCH" || "$BRANCH" == "main" ]]; then
  emit_status skipped_on_main
  exit 0
fi

if [[ "$DRY_RUN" == "true" ]]; then
  emit_status skipped_dry_run
  exit 0
fi

if ! git fetch origin main >/dev/null 2>&1; then
  emit_status error_fetch
  exit 1
fi

if git merge origin/main --no-edit >/dev/null 2>&1; then
  emit_status success
  exit 0
fi

emit_status conflict
exit 2
