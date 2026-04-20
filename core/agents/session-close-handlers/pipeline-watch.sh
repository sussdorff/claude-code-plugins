#!/usr/bin/env bash
# pipeline-watch.sh - Watch the GitHub Actions run for a pushed commit and block until it finishes.
#
# Usage: pipeline-watch.sh [--dry-run] [--repo-dir <dir>] [--sha <sha>] [--timeout <seconds>]
#
# Defaults:
#   --repo-dir : current git top-level
#   --sha      : HEAD of --repo-dir
#   --timeout  : 30 seconds to wait for a run to register after push
#
# Outputs (stdout, KV lines):
#   PIPELINE_STATUS=passed|failed|skipped_no_gh|skipped_not_authed|skipped_no_workflow|skipped_dry_run
#   PIPELINE_RUN_ID=<id>       (on passed/failed)
#   PIPELINE_RUN_URL=<url>     (on passed/failed, if resolvable)
#   PIPELINE_ERROR=<msg>       (optional, on unexpected issues)
#
# Exit codes:
#   0 - passed or any "skipped_*" state (non-blocking for the caller)
#   1 - failed (caller MUST NOT close beads)

set -uo pipefail

DRY_RUN=false
REPO_DIR=""
SHA=""
TIMEOUT=30

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --repo-dir) REPO_DIR="${2:-}"; shift 2 ;;
    --sha) SHA="${2:-}"; shift 2 ;;
    --timeout) TIMEOUT="${2:-30}"; shift 2 ;;
    *) shift ;;
  esac
done

if [[ "$DRY_RUN" == "true" ]]; then
  echo "PIPELINE_STATUS=skipped_dry_run"
  exit 0
fi

if [[ -z "$REPO_DIR" ]]; then
  REPO_DIR="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"
fi

if [[ -z "$REPO_DIR" || ! -d "$REPO_DIR" ]]; then
  echo "PIPELINE_STATUS=skipped_no_gh"
  echo "PIPELINE_ERROR=no_repo_dir"
  exit 0
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "PIPELINE_STATUS=skipped_no_gh"
  exit 0
fi

# Check auth — unauthenticated gh is useless here
if ! gh auth status >/dev/null 2>&1; then
  echo "PIPELINE_STATUS=skipped_not_authed"
  exit 0
fi

cd "$REPO_DIR" || {
  echo "PIPELINE_STATUS=skipped_no_gh"
  echo "PIPELINE_ERROR=cannot_cd_repo_dir"
  exit 0
}

# Only watch runs on GitHub remotes
REMOTE_URL="$(git config --get remote.origin.url 2>/dev/null || echo "")"
if [[ "$REMOTE_URL" != *"github.com"* && "$REMOTE_URL" != *"github.com:"* ]]; then
  echo "PIPELINE_STATUS=skipped_no_workflow"
  echo "PIPELINE_ERROR=non_github_remote"
  exit 0
fi

if [[ -z "$SHA" ]]; then
  SHA="$(git rev-parse HEAD 2>/dev/null || echo "")"
fi

if [[ -z "$SHA" ]]; then
  echo "PIPELINE_STATUS=skipped_no_workflow"
  echo "PIPELINE_ERROR=could_not_resolve_sha"
  exit 0
fi

# Poll for a run to register on GitHub after the push (it can take a few seconds)
RUN_ID=""
END_TS=$(( $(date +%s) + TIMEOUT ))
while (( $(date +%s) < END_TS )); do
  RUN_ID="$(gh run list --commit "$SHA" --limit 1 --json databaseId --jq '.[0].databaseId' 2>/dev/null || echo "")"
  if [[ -n "$RUN_ID" ]]; then
    break
  fi
  sleep 3
done

if [[ -z "$RUN_ID" ]]; then
  # No workflow file, or run simply never registered — treat as non-blocking skip
  echo "PIPELINE_STATUS=skipped_no_workflow"
  exit 0
fi

# Resolve run URL once, best-effort
RUN_URL="$(gh run view "$RUN_ID" --json url --jq '.url' 2>/dev/null || echo "")"

# Watch the run — blocks until complete, non-zero exit on failure
gh run watch "$RUN_ID" --exit-status --interval 15 >/dev/null 2>&1
WATCH_EXIT=$?

echo "PIPELINE_RUN_ID=$RUN_ID"
[[ -n "$RUN_URL" ]] && echo "PIPELINE_RUN_URL=$RUN_URL"

if [[ "$WATCH_EXIT" -eq 0 ]]; then
  echo "PIPELINE_STATUS=passed"
  exit 0
fi

echo "PIPELINE_STATUS=failed"
exit 1
