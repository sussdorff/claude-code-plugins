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
#   PIPELINE_RUN_ID=<id>       (on passed/failed, when a run existed)
#   PIPELINE_RUN_URL=<url>     (on passed/failed, if resolvable)
#   PIPELINE_ERROR=<msg>       (on failed/skipped when the reason is non-obvious, e.g. no_run_registered)
#
# Exit codes:
#   0 - passed or any "skipped_*" state (non-blocking for the caller)
#   1 - failed (caller MUST NOT close beads). Includes:
#       - CI ran and failed                            → PIPELINE_ERROR unset (normal failure)
#       - push-triggered workflow exists but no run
#         registered within --timeout                  → PIPELINE_ERROR=no_run_registered

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

# Detect whether this repo has any push-triggered GitHub Actions workflow.
# Used to distinguish "no workflow (fine, skip)" from "workflow expected but no
# run registered (blocking — runner offline, webhook broken, Actions disabled)".
#
# Matches the three YAML forms:
#   on: push
#   on: [push, pull_request]
#   on:\n  push:\n    branches: [main]
#
# False-positive tolerance: if "push" appears in a non-trigger context (e.g. a
# job step referencing a push action), we may falsely think a workflow is
# push-triggered. That pushes us toward over-reporting FAIL, which is the safe
# direction — a false FAIL just keeps a bead open for manual inspection.
has_push_triggered_workflow() {
  local dir="$1/.github/workflows"
  [[ -d "$dir" ]] || return 1

  local wf
  for wf in "$dir"/*.yml "$dir"/*.yaml; do
    [[ -f "$wf" ]] || continue

    # Form 1: "on: push" (scalar trigger)
    if grep -qE '^on:[[:space:]]+push([[:space:]]|$)' "$wf" 2>/dev/null; then
      return 0
    fi
    # Form 2: "on: [push, ...]" or "on: [..., push, ...]" (sequence)
    if grep -qE '^on:[[:space:]]*\[[^]]*\bpush\b[^]]*\]' "$wf" 2>/dev/null; then
      return 0
    fi
    # Form 3: multi-line "on:" mapping with "push:" key
    # awk: print lines between "on:" (a line with no indent) and the next
    # non-indented top-level key. Then grep for indented "push:".
    if awk '
      /^on:[[:space:]]*$/ { in_on=1; next }
      in_on && /^[^[:space:]#]/ { in_on=0 }
      in_on { print }
    ' "$wf" 2>/dev/null | grep -qE '^[[:space:]]+push:'; then
      return 0
    fi
  done

  return 1
}

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
  # Distinguish two very different cases:
  #   (a) this repo has NO push-triggered workflow → genuinely no CI → skip
  #   (b) a push-triggered workflow exists but NO run registered within timeout
  #       → something is broken (self-hosted runner offline, webhook down,
  #         Actions disabled on the repo, branch protection override, etc.)
  #       → fail-closed so beads stay in_progress until someone investigates
  if has_push_triggered_workflow "$REPO_DIR"; then
    echo "PIPELINE_STATUS=failed"
    echo "PIPELINE_ERROR=no_run_registered"
    exit 1
  fi
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
