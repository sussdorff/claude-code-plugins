#!/usr/bin/env bash
# merge-feature.sh - merge a feature branch into main (in the main repo)
#
# Usage: merge-feature.sh --main-repo <dir> --branch <branch> [--dry-run]
#
# Called by session-close Step 15 (feature->main merge) immediately after
# Step 14 (second merge from main into feature). This is the race-window-
# minimizing step of the double-merge strategy.
#
# Behaviour:
#   - Always uses --no-ff so the merge is a visible commit in main's history.
#   - In --dry-run, reports what would happen without merging.
#   - On merge conflict, exit 2 — caller MUST stop session-close.
#
# Output (stdout, KV lines):
#   MERGE_FEATURE_STATUS=success|skipped_dry_run|conflict|error_args
#   MERGE_FEATURE_BRANCH=<branch>
#
# Exit codes:
#   0 - success or dry-run skip
#   1 - arg / environment error (missing flags, main_repo not a repo)
#   2 - merge conflict — caller MUST stop

set -uo pipefail

DRY_RUN=false
MAIN_REPO=""
BRANCH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --main-repo) MAIN_REPO="${2:-}"; shift 2 ;;
    --branch) BRANCH="${2:-}"; shift 2 ;;
    *) shift ;;
  esac
done

if [[ -z "$MAIN_REPO" || -z "$BRANCH" ]]; then
  echo "MERGE_FEATURE_STATUS=error_args"
  echo "MERGE_FEATURE_ERROR=missing_main_repo_or_branch"
  exit 1
fi

if [[ ! -d "$MAIN_REPO" ]]; then
  echo "MERGE_FEATURE_STATUS=error_args"
  echo "MERGE_FEATURE_BRANCH=$BRANCH"
  echo "MERGE_FEATURE_ERROR=main_repo_not_a_directory"
  exit 1
fi

echo "MERGE_FEATURE_BRANCH=$BRANCH"

if [[ "$DRY_RUN" == "true" ]]; then
  echo "MERGE_FEATURE_STATUS=skipped_dry_run"
  exit 0
fi

if git -C "$MAIN_REPO" merge --no-ff "$BRANCH" -m "merge: $BRANCH" >/dev/null 2>&1; then
  echo "MERGE_FEATURE_STATUS=success"
  exit 0
fi

echo "MERGE_FEATURE_STATUS=conflict"
exit 2
