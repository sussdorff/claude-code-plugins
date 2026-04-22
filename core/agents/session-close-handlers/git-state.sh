#!/usr/bin/env bash
# git-state.sh — Read all git state session-close needs in ONE call.
#
# Usage: git-state.sh [--repo-dir <dir>] [--log-depth <n>]
#
# Outputs a single JSON document on stdout with all state fields needed by
# session-close to understand the current situation without additional git calls.
#
# Fields:
#   branch          string  current branch name
#   head_sha        string  full HEAD SHA
#   in_worktree     bool    true if running in a git worktree
#   main_repo       string  path to the main git repo (empty if not in worktree)
#   handoff_file    string  path to .worktree-handoff.json (empty if missing)
#   commits_ahead   array   [{sha, msg}] commits on HEAD not in origin/main (max log_depth)
#   existing_tag    string  version tag on HEAD, or "" if none
#   dirty           bool    true if working tree has uncommitted changes
#   remote_url      string  origin remote URL
#   main_head_sha   string  HEAD of main branch in main repo (empty if n/a)
#
# Why this exists:
#   session-close was making 5-10 exploratory git calls to understand state.
#   This script collapses them into one Bash tool use.
#
# Exit codes:
#   0 — success
#   1 — not in a git repo

set -uo pipefail

REPO_DIR=""
LOG_DEPTH=30

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-dir) REPO_DIR="${2:-}"; shift 2 ;;
    --log-depth) LOG_DEPTH="${2:-30}"; shift 2 ;;
    *) shift ;;
  esac
done

if [[ -n "$REPO_DIR" ]]; then
  cd "$REPO_DIR" || { echo '{"error":"cannot_cd_repo_dir"}'; exit 1; }
fi

# Confirm we're in a git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo '{"error":"not_in_git_repo"}'
  exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
BRANCH="$(git branch --show-current 2>/dev/null || echo "")"
HEAD_SHA="$(git rev-parse HEAD 2>/dev/null || echo "")"

# Worktree detection: common git dir lives in the main repo
GIT_COMMON_DIR="$(git rev-parse --git-common-dir 2>/dev/null || echo "")"
IN_WORKTREE=false
MAIN_REPO=""
MAIN_HEAD_SHA=""
if [[ -n "$GIT_COMMON_DIR" ]]; then
  GIT_COMMON_DIR_ABS="$(realpath "$GIT_COMMON_DIR" 2>/dev/null || echo "$GIT_COMMON_DIR")"
  MAIN_REPO_CANDIDATE="${GIT_COMMON_DIR_ABS%/.git}"
  if [[ "$MAIN_REPO_CANDIDATE" != "$REPO_ROOT" ]]; then
    IN_WORKTREE=true
    MAIN_REPO="$MAIN_REPO_CANDIDATE"
    MAIN_HEAD_SHA="$(git -C "$MAIN_REPO" rev-parse main 2>/dev/null || echo "")"
  fi
fi

# Commits ahead of origin/main (up to LOG_DEPTH)
COMMITS_AHEAD_JSON="[]"
if git fetch origin main --quiet 2>/dev/null; then
  COMMITS_AHEAD_JSON=$(git log --oneline "origin/main..HEAD" --max-count="$LOG_DEPTH" \
    --format='{"sha":"%h","msg":"%s"}' 2>/dev/null | jq -s '.' 2>/dev/null || echo "[]")
fi

# Existing version tag on HEAD
EXISTING_TAG="$(git tag --points-at HEAD 2>/dev/null | grep -E '^v[0-9]' | head -1 || echo "")"

# Dirty working tree
DIRTY=false
if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
  DIRTY=true
fi

# Remote URL
REMOTE_URL="$(git config --get remote.origin.url 2>/dev/null || echo "")"

# Handoff file (worktree scenario)
HANDOFF_FILE=""
if [[ -f "$REPO_ROOT/.worktree-handoff.json" ]]; then
  HANDOFF_FILE="$REPO_ROOT/.worktree-handoff.json"
fi

jq -cn \
  --arg branch "$BRANCH" \
  --arg head_sha "$HEAD_SHA" \
  --argjson in_worktree "$IN_WORKTREE" \
  --arg main_repo "$MAIN_REPO" \
  --arg handoff_file "$HANDOFF_FILE" \
  --argjson commits_ahead "$COMMITS_AHEAD_JSON" \
  --arg existing_tag "$EXISTING_TAG" \
  --argjson dirty "$DIRTY" \
  --arg remote_url "$REMOTE_URL" \
  --arg main_head_sha "$MAIN_HEAD_SHA" \
  '{
    branch:        $branch,
    head_sha:      $head_sha,
    in_worktree:   $in_worktree,
    main_repo:     $main_repo,
    handoff_file:  $handoff_file,
    commits_ahead: $commits_ahead,
    existing_tag:  $existing_tag,
    dirty:         $dirty,
    remote_url:    $remote_url,
    main_head_sha: $main_head_sha
  }'
