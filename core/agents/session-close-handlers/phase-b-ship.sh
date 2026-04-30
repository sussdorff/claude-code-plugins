#!/usr/bin/env bash
# phase-b-ship.sh - Phase B ship batch handler
#
# Consolidates Steps 13, 14, 14b, 15, 15b, 16, 16a, 16c from session-close into a
# single script that emits one JSON document. Replaces ~7 individual handler
# calls with one tool use.
#
# Steps executed (in order):
#   13: Kill worktree dev processes (portless namespace)
#   14: Second merge from main (merge-from-main.sh)
#   14b: Scan main repo working tree for uncommitted generated files
#   15: Merge feature branch into main (merge-feature.sh)
#   15b: Version bump + create tag (version.sh)
#   16: Push + tag push
#   16a: Pipeline watch (pipeline-watch.sh)
#   16c: Sync plugin cache (sync-plugin-cache.sh)
#
# Usage:
#   phase-b-ship.sh [options]
#
# Options:
#   --dry-run            Preview all steps, no git changes
#   --skip-push          Skip step 16 (push + tag push)
#   --skip-pipeline      Skip step 16a (pipeline watch)
#   --main-repo <dir>    Path to the main repo root (for worktree scenarios)
#   --branch <branch>    Current feature branch name
#   --namespace <ns>     Portless namespace for step 13 process kill
#
# Emits a single JSON document on stdout; stderr for human-readable progress.
#
# Exit codes:
#   0 - all steps ok or any outcome the caller can reason about (incl partial failure)
#   2 - merge conflict on step 14 or 15 (caller MUST stop, previous work preserved)
#   1 - internal/unparseable error
#
# Idempotency: safe to re-run. All merges are no-ops if already merged.
# Version bump is no-op if already at the next version. Push is no-op if
# already pushed (git push exits 0 when up-to-date).
#
# Schema: phase-b-ship.schema.json

set -uo pipefail

# ---------------------------------------------------------------------------
# Flag parsing
# ---------------------------------------------------------------------------
DRY_RUN=false
SKIP_PUSH=false
SKIP_PIPELINE=false
MAIN_REPO=""
BRANCH=""
NAMESPACE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)       DRY_RUN=true;              shift ;;
    --skip-push)     SKIP_PUSH=true;            shift ;;
    --skip-pipeline) SKIP_PIPELINE=true;        shift ;;
    --main-repo)     MAIN_REPO="${2:-}";        shift 2 ;;
    --branch)        BRANCH="${2:-}";           shift 2 ;;
    --namespace)     NAMESPACE="${2:-}";        shift 2 ;;
    *) shift ;;
  esac
done

DRY_RUN_ARGS=()
if [[ "$DRY_RUN" == "true" ]]; then
  DRY_RUN_ARGS=(--dry-run)
fi

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"
if [[ -z "$REPO_ROOT" ]]; then
  echo '{"error":"not_in_git_repo"}' >&2
  exit 1
fi

HANDLERS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect worktree: common git dir lives in the main repo
GIT_COMMON_DIR="$(git rev-parse --git-common-dir 2>/dev/null || echo "")"
MAIN_REPO_DETECTED=""
if [[ -n "$GIT_COMMON_DIR" ]]; then
  GIT_COMMON_DIR="$(realpath "$GIT_COMMON_DIR" 2>/dev/null || echo "$GIT_COMMON_DIR")"
  MAIN_REPO_DETECTED="${GIT_COMMON_DIR%/.git}"
fi
IN_WORKTREE=false
if [[ -n "$MAIN_REPO_DETECTED" && "$MAIN_REPO_DETECTED" != "$REPO_ROOT" ]]; then
  IN_WORKTREE=true
  [[ -z "$MAIN_REPO" ]] && MAIN_REPO="$MAIN_REPO_DETECTED"
fi

[[ -z "$BRANCH" ]] && BRANCH="$(git branch --show-current 2>/dev/null || echo "")"
[[ -z "$NAMESPACE" ]] && NAMESPACE="$(basename "$REPO_ROOT")"

GIT_WORK_DIR="${MAIN_REPO:-$REPO_ROOT}"

# ---------------------------------------------------------------------------
# Result accumulators
# ---------------------------------------------------------------------------
KILL_PROCS_STATUS="skipped"
KILL_PROCS_KILLED=()

SECOND_MERGE_STATUS="not_attempted"
SECOND_MERGE_DETAIL=""

MERGE_FEATURE_STATUS="not_attempted"
MERGE_FEATURE_DETAIL=""

MAIN_SCAN_STATUS="skipped"
MAIN_SCAN_COMMITTED_FILES=()
MAIN_SCAN_ADVISORY_FILES=()
MAIN_SCAN_COMMITTED=false

VERSION_STATUS="not_attempted"
VERSION_TAG=""
VERSION_VER=""

PUSH_GATE_STATUS="skipped"
PUSH_GATE_DETAIL=""
PUSH_GATE_WAITED=0

PUSH_STATUS="not_attempted"
PUSH_DETAIL=""

PIPELINE_STATUS="not_attempted"
PIPELINE_RUN_URL=""

PLUGIN_CACHE_STATUS="skipped"
PLUGIN_CACHE_DETAIL=""

# ---------------------------------------------------------------------------
# Step 13: Kill worktree dev processes
# ---------------------------------------------------------------------------
echo "==> Step 13: Kill worktree dev processes" >&2

if [[ "$IN_WORKTREE" == "true" ]]; then
  if [[ "$DRY_RUN" == "true" ]]; then
    KILL_PROCS_STATUS="skipped"
    echo "    [dry-run] would kill portless processes for namespace: $NAMESPACE" >&2
  else
    # Kill portless-wrapped processes for this worktree namespace
    KILLED_COUNT=0
    for pattern in "portless ${NAMESPACE}-api" "portless ${NAMESPACE} "; do
      PIDS=$(pgrep -f "$pattern" 2>/dev/null || true)
      if [[ -n "$PIDS" ]]; then
        pkill -f "$pattern" 2>/dev/null || true
        KILL_PROCS_KILLED+=("$pattern")
        (( KILLED_COUNT++ ))
      fi
    done
    if [[ "$KILLED_COUNT" -gt 0 ]]; then
      KILL_PROCS_STATUS="ok"
      echo "    killed $KILLED_COUNT process group(s) for namespace $NAMESPACE" >&2
    else
      KILL_PROCS_STATUS="ok"
      echo "    no portless processes found for namespace $NAMESPACE" >&2
    fi
  fi
else
  echo "    not in worktree, skipping" >&2
fi

# ---------------------------------------------------------------------------
# Step 14: Second merge from main
# ---------------------------------------------------------------------------
echo "==> Step 14: Second merge from main" >&2

MERGE2_OUT=$(bash "$HANDLERS_DIR/merge-from-main.sh" \
  "${DRY_RUN_ARGS[@]}" --label "second" 2>&1) || MERGE2_EXIT=$?
MERGE2_EXIT=${MERGE2_EXIT:-0}

MERGE2_RAW=$(echo "$MERGE2_OUT" | grep '^MERGE_FROM_MAIN_STATUS=' | cut -d= -f2)

case "$MERGE2_RAW" in
  success)         SECOND_MERGE_STATUS="ok"; SECOND_MERGE_DETAIL="merged origin/main" ;;
  skipped_on_main) SECOND_MERGE_STATUS="skipped"; SECOND_MERGE_DETAIL="branch is main" ;;
  skipped_dry_run) SECOND_MERGE_STATUS="skipped"; SECOND_MERGE_DETAIL="dry-run" ;;
  conflict)
    SECOND_MERGE_STATUS="conflict"
    SECOND_MERGE_DETAIL="merge conflict — resolve and re-run with --ship-only"
    jq -cn \
      --argjson killed "$(printf '%s\n' "${KILL_PROCS_KILLED[@]+"${KILL_PROCS_KILLED[@]}"}" | jq -R . | jq -s . || echo '[]')" \
      --arg kps "$KILL_PROCS_STATUS" \
      --arg sms "$SECOND_MERGE_STATUS" --arg smd "$SECOND_MERGE_DETAIL" \
      '{
        kill_procs: {status:$kps, killed:$killed},
        second_merge: {status:$sms, detail:$smd},
        main_repo_scan: {status:"not_attempted", committed_files:[], advisory_files:[]},
        merge_feature: {status:"not_attempted", detail:""},
        version: {status:"not_attempted", tag:"", version:""},
        push_gate: {status:"not_attempted", detail:"", waited_seconds:0},
        push: {status:"not_attempted", detail:""},
        pipeline: {status:"not_attempted", run_url:""},
        plugin_cache: {status:"not_attempted", detail:""}
      }'
    exit 2
    ;;
  error_fetch)
    SECOND_MERGE_STATUS="failed"
    SECOND_MERGE_DETAIL="git fetch origin main failed"
    ;;
  *)
    SECOND_MERGE_STATUS="${MERGE2_RAW:-unknown}"
    SECOND_MERGE_DETAIL=""
    ;;
esac
echo "    merge status: $SECOND_MERGE_STATUS" >&2

# ---------------------------------------------------------------------------
# Step 14b: Scan main repo working tree for uncommitted generated files
# ---------------------------------------------------------------------------
# Before merging the feature branch into main, check if the main repo working
# tree has uncommitted changes. Generated files (lockfiles, CHANGELOG.md,
# files in generated/ dirs) are auto-staged and committed. Non-generated
# uncommitted files are reported as an advisory warning (non-blocking).
# ---------------------------------------------------------------------------
echo "==> Step 14b: Scan main repo for uncommitted generated files" >&2

if [[ "$IN_WORKTREE" == "true" && -n "$MAIN_REPO" ]]; then
  MAIN_PORCELAIN=$(git -C "$MAIN_REPO" status --porcelain 2>/dev/null || true)
  if [[ -z "$MAIN_PORCELAIN" ]]; then
    MAIN_SCAN_STATUS="clean"
    echo "    main repo working tree is clean" >&2
  else
    # Classify each changed file as generated or non-generated
    _is_generated_file() {
      local file="$1"
      local base
      base=$(basename "$file")
      # Known generated basenames
      case "$base" in
        bun.lockb|package-lock.json|yarn.lock|pnpm-lock.yaml|CHANGELOG.md|CHANGELOG.rst)
          return 0 ;;
        *.lock)
          return 0 ;;
      esac
      # Files under a generated/ directory segment
      if [[ "$file" == */generated/* || "$file" == generated/* ]]; then
        return 0
      fi
      return 1
    }

    while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      file="${line:3}"
      [[ -z "$file" ]] && continue
      if _is_generated_file "$file"; then
        MAIN_SCAN_COMMITTED_FILES+=("$file")
      else
        MAIN_SCAN_ADVISORY_FILES+=("$file")
      fi
    done < <(echo "$MAIN_PORCELAIN")

    echo "    generated: ${#MAIN_SCAN_COMMITTED_FILES[@]}, non-generated (advisory): ${#MAIN_SCAN_ADVISORY_FILES[@]}" >&2

    # Auto-commit generated files
    if [[ ${#MAIN_SCAN_COMMITTED_FILES[@]} -gt 0 ]]; then
      if [[ "$DRY_RUN" == "true" ]]; then
        MAIN_SCAN_STATUS="dry_run"
        echo "    [dry-run] would commit ${#MAIN_SCAN_COMMITTED_FILES[@]} generated file(s) to main" >&2
      else
        git -C "$MAIN_REPO" add -- "${MAIN_SCAN_COMMITTED_FILES[@]}"
        if git -C "$MAIN_REPO" commit -m "chore: commit generated files before bead merge ($BRANCH)" 2>/dev/null; then
          MAIN_SCAN_COMMITTED=true
          echo "    committed ${#MAIN_SCAN_COMMITTED_FILES[@]} generated file(s) to main" >&2
          MAIN_SCAN_STATUS="committed"
        else
          MAIN_SCAN_STATUS="commit_failed"
          echo "    WARN: could not commit generated files in main repo" >&2
        fi
      fi
    fi

    # Report advisory files (non-blocking)
    if [[ ${#MAIN_SCAN_ADVISORY_FILES[@]} -gt 0 ]]; then
      case "$MAIN_SCAN_STATUS" in
        committed)   MAIN_SCAN_STATUS="committed_advisory" ;;
        dry_run)     MAIN_SCAN_STATUS="advisory" ;;
        *)           MAIN_SCAN_STATUS="advisory" ;;
      esac
      echo "    ADVISORY: ${#MAIN_SCAN_ADVISORY_FILES[@]} non-generated file(s) uncommitted in main repo:" >&2
      for f in "${MAIN_SCAN_ADVISORY_FILES[@]}"; do
        echo "      - $f" >&2
      done
    fi

    # If nothing changed the status from its initial "skipped", the tree was clean
    [[ "$MAIN_SCAN_STATUS" == "skipped" ]] && MAIN_SCAN_STATUS="clean"
  fi
else
  echo "    skipped (not in worktree or main repo not set)" >&2
fi

# ---------------------------------------------------------------------------
# Step 15: Merge feature into main
# ---------------------------------------------------------------------------
echo "==> Step 15: Merge feature into main" >&2

if [[ "$IN_WORKTREE" == "true" && "$BRANCH" != "main" && -n "$MAIN_REPO" ]]; then
  MF_OUT=$(bash "$HANDLERS_DIR/merge-feature.sh" \
    --main-repo "$MAIN_REPO" \
    --branch "$BRANCH" \
    "${DRY_RUN_ARGS[@]}" 2>&1) || MF_EXIT=$?
  MF_EXIT=${MF_EXIT:-0}

  MF_RAW=$(echo "$MF_OUT" | grep '^MERGE_FEATURE_STATUS=' | cut -d= -f2)
  case "$MF_RAW" in
    success)          MERGE_FEATURE_STATUS="ok"; MERGE_FEATURE_DETAIL="merged $BRANCH into main" ;;
    skipped_dry_run)  MERGE_FEATURE_STATUS="skipped"; MERGE_FEATURE_DETAIL="dry-run" ;;
    conflict)
      MERGE_FEATURE_STATUS="conflict"
      MERGE_FEATURE_DETAIL="merge conflict on feature->main — resolve manually"
      jq -cn \
        --argjson killed "$(printf '%s\n' "${KILL_PROCS_KILLED[@]+"${KILL_PROCS_KILLED[@]}"}" | jq -R . | jq -s . || echo '[]')" \
        --argjson msc_committed "$(printf '%s\n' "${MAIN_SCAN_COMMITTED_FILES[@]+"${MAIN_SCAN_COMMITTED_FILES[@]}"}" | jq -R . | jq -s . || echo '[]')" \
        --argjson msc_advisory "$(printf '%s\n' "${MAIN_SCAN_ADVISORY_FILES[@]+"${MAIN_SCAN_ADVISORY_FILES[@]}"}" | jq -R . | jq -s . || echo '[]')" \
        --arg kps "$KILL_PROCS_STATUS" \
        --arg sms "$SECOND_MERGE_STATUS" --arg smd "$SECOND_MERGE_DETAIL" \
        --arg mscs "$MAIN_SCAN_STATUS" \
        --arg mfs "$MERGE_FEATURE_STATUS" --arg mfd "$MERGE_FEATURE_DETAIL" \
        '{
          kill_procs: {status:$kps, killed:$killed},
          second_merge: {status:$sms, detail:$smd},
          main_repo_scan: {status:$mscs, committed_files:$msc_committed, advisory_files:$msc_advisory},
          merge_feature: {status:$mfs, detail:$mfd},
          version: {status:"not_attempted", tag:"", version:""},
          push_gate: {status:"not_attempted", detail:"", waited_seconds:0},
          push: {status:"not_attempted", detail:""},
          pipeline: {status:"not_attempted", run_url:""},
          plugin_cache: {status:"not_attempted", detail:""}
        }'
      exit 2
      ;;
    error_args|*)
      MERGE_FEATURE_STATUS="failed"
      MERGE_FEATURE_DETAIL="${MF_RAW:-unknown}"
      # Unknown/error status from merge-feature — emit partial JSON and abort
      jq -cn \
        --argjson killed "$(printf '%s\n' "${KILL_PROCS_KILLED[@]+"${KILL_PROCS_KILLED[@]}"}" | jq -R . | jq -s . || echo '[]')" \
        --argjson msc_committed "$(printf '%s\n' "${MAIN_SCAN_COMMITTED_FILES[@]+"${MAIN_SCAN_COMMITTED_FILES[@]}"}" | jq -R . | jq -s . || echo '[]')" \
        --argjson msc_advisory "$(printf '%s\n' "${MAIN_SCAN_ADVISORY_FILES[@]+"${MAIN_SCAN_ADVISORY_FILES[@]}"}" | jq -R . | jq -s . || echo '[]')" \
        --arg kps "$KILL_PROCS_STATUS" \
        --arg sms "$SECOND_MERGE_STATUS" --arg smd "$SECOND_MERGE_DETAIL" \
        --arg mscs "$MAIN_SCAN_STATUS" \
        --arg mfs "$MERGE_FEATURE_STATUS" --arg mfd "$MERGE_FEATURE_DETAIL" \
        '{
          kill_procs: {status:$kps, killed:$killed},
          second_merge: {status:$sms, detail:$smd},
          main_repo_scan: {status:$mscs, committed_files:$msc_committed, advisory_files:$msc_advisory},
          merge_feature: {status:$mfs, detail:$mfd},
          version: {status:"not_attempted", tag:"", version:""},
          push_gate: {status:"not_attempted", detail:"", waited_seconds:0},
          push: {status:"not_attempted", detail:""},
          pipeline: {status:"not_attempted", run_url:""},
          plugin_cache: {status:"not_attempted", detail:""}
        }'
      exit 2
      ;;
  esac
else
  MERGE_FEATURE_STATUS="skipped"
  if [[ "$BRANCH" == "main" ]]; then
    MERGE_FEATURE_DETAIL="already on main"
  elif [[ "$IN_WORKTREE" == "false" ]]; then
    MERGE_FEATURE_DETAIL="not in worktree"
  else
    MERGE_FEATURE_DETAIL="main-repo not set"
  fi
fi
echo "    merge-feature status: $MERGE_FEATURE_STATUS" >&2

# ---------------------------------------------------------------------------
# Step 15b: Version bump + tag
# ---------------------------------------------------------------------------
echo "==> Step 15b: Version bump" >&2

TAG_PUSHED=false

# Idempotency: if HEAD is already tagged, reuse that tag instead of bumping again
EXISTING_TAG=$(git -C "$GIT_WORK_DIR" tag --points-at HEAD 2>/dev/null | head -1)
if [[ -n "$EXISTING_TAG" ]]; then
  VERSION_TAG="$EXISTING_TAG"
  VERSION_VER=$(echo "$EXISTING_TAG" | sed 's/^v//')
  VERSION_STATUS="ok"
  echo "    HEAD already tagged as $EXISTING_TAG — skipping version bump" >&2
else
  VER_OUT=$(bash "$HANDLERS_DIR/version.sh" "${DRY_RUN_ARGS[@]}" 2>&1) || VER_EXIT=$?
  VER_EXIT=${VER_EXIT:-0}

  if [[ "$VER_EXIT" -eq 0 ]]; then
    TAG_PENDING=$(echo "$VER_OUT" | grep '^TAG_PENDING=' | cut -d= -f2 || echo "")
    TAG_MESSAGE=$(echo "$VER_OUT" | grep '^TAG_MESSAGE=' | cut -d= -f2- || echo "")
    VERSION_TAG="$TAG_PENDING"
    VERSION_VER=$(echo "$TAG_PENDING" | sed 's/^v//')

    if [[ "$DRY_RUN" == "false" && -n "$TAG_PENDING" ]]; then
      # Commit version bump (version.sh has already staged VERSION + plugin.json files)
      COMMIT_OUT=$(git -C "$GIT_WORK_DIR" commit -m "chore: bump version to $VERSION_VER" 2>&1) || COMMIT_EXIT=$?
      COMMIT_EXIT=${COMMIT_EXIT:-0}
      if [[ "$COMMIT_EXIT" -ne 0 ]]; then
        VERSION_STATUS="failed"
        echo "    version commit failed (exit $COMMIT_EXIT): $COMMIT_OUT" >&2
      else
        # Create the tag
        TAG_OUT=$(git -C "$GIT_WORK_DIR" tag -a "$TAG_PENDING" -m "${TAG_MESSAGE:-Release $VERSION_VER}" 2>&1) || TAG_EXIT=$?
        TAG_EXIT=${TAG_EXIT:-0}
        if [[ "$TAG_EXIT" -ne 0 ]]; then
          VERSION_STATUS="failed"
          echo "    version tag failed (exit $TAG_EXIT): $TAG_OUT" >&2
        else
          VERSION_STATUS="ok"
          echo "    version $VERSION_VER tagged as $TAG_PENDING" >&2
        fi
      fi
    elif [[ "$DRY_RUN" == "true" ]]; then
      VERSION_STATUS="ok"
      echo "    [dry-run] would bump to $VERSION_VER, tag $TAG_PENDING" >&2
    else
      VERSION_STATUS="ok"
    fi
  else
    VERSION_STATUS="failed"
    echo "    version.sh exited $VER_EXIT" >&2
  fi
fi
echo "    version status: $VERSION_STATUS (tag: ${VERSION_TAG:-none})" >&2

# ---------------------------------------------------------------------------
# Step 15c: Push Gate — defer push if a CI pipeline is already running
# ---------------------------------------------------------------------------
# Modes:
#   skip (default): if CI busy → defer push, work stays merged locally,
#                   next session-close pushes accumulated work in one go.
#                   Avoids the "10 parallel beads = 10 CI runs" pattern.
#   wait:           block until CI free (timeout PUSH_GATE_TIMEOUT, default 600s)
#   force:          ignore CI state, push immediately
#
# Override via env: PUSH_GATE_MODE=skip|wait|force
# ---------------------------------------------------------------------------
echo "==> Step 15c: Push gate" >&2

PUSH_GATE_MODE="${PUSH_GATE_MODE:-skip}"        # default: skip (defer push)
PUSH_GATE_TIMEOUT="${PUSH_GATE_TIMEOUT:-600}"   # only used in wait mode
PUSH_GATE_INTERVAL=30
DEFER_PUSH=false

if [[ "$SKIP_PUSH" == "true" || "$DRY_RUN" == "true" ]]; then
  PUSH_GATE_STATUS="skipped"
  PUSH_GATE_DETAIL="${DRY_RUN:+dry-run}${SKIP_PUSH:+skip-push}"
  echo "    skipped (${PUSH_GATE_DETAIL})" >&2
elif [[ "$PUSH_GATE_MODE" == "force" ]]; then
  PUSH_GATE_STATUS="ok"
  PUSH_GATE_DETAIL="forced (ignored CI state)"
  echo "    forced — ignoring CI state" >&2
elif ! command -v gh &>/dev/null; then
  PUSH_GATE_STATUS="skipped"
  PUSH_GATE_DETAIL="gh not available"
  echo "    skipped (gh not available)" >&2
else
  RUNNING=$(gh run list --status in_progress --limit 5 --json databaseId \
    2>/dev/null | jq 'length' 2>/dev/null || echo "0")

  if [[ "$RUNNING" -eq 0 ]]; then
    PUSH_GATE_STATUS="ok"
    PUSH_GATE_DETAIL="no in-progress pipelines"
    echo "    push gate: clear" >&2
  elif [[ "$PUSH_GATE_MODE" == "skip" ]]; then
    # Default behaviour: defer push to next session-close
    PUSH_GATE_STATUS="deferred"
    PUSH_GATE_DETAIL="$RUNNING pipeline(s) running — push deferred, work stays in local main"
    DEFER_PUSH=true
    echo "    push deferred — $RUNNING CI run(s) active; next session-close pushes accumulated work" >&2
  else
    # wait mode: block until clear or timeout
    GATE_START=$(date +%s)
    while [[ "$RUNNING" -gt 0 ]]; do
      NOW=$(date +%s)
      PUSH_GATE_WAITED=$(( NOW - GATE_START ))
      if [[ "$PUSH_GATE_WAITED" -ge "$PUSH_GATE_TIMEOUT" ]]; then
        PUSH_GATE_STATUS="timeout"
        PUSH_GATE_DETAIL="waited ${PUSH_GATE_WAITED}s, $RUNNING pipeline(s) still running — proceeding anyway"
        echo "    push gate timeout after ${PUSH_GATE_WAITED}s — proceeding" >&2
        break
      fi
      echo "    push gate (wait mode): $RUNNING pipeline(s) running, polling ${PUSH_GATE_INTERVAL}s (elapsed: ${PUSH_GATE_WAITED}s)" >&2
      sleep "$PUSH_GATE_INTERVAL"
      RUNNING=$(gh run list --status in_progress --limit 5 --json databaseId \
        2>/dev/null | jq 'length' 2>/dev/null || echo "0")
    done
    if [[ "$RUNNING" -eq 0 && "$PUSH_GATE_STATUS" != "timeout" ]]; then
      PUSH_GATE_STATUS="ok"
      PUSH_GATE_DETAIL="cleared after ${PUSH_GATE_WAITED}s wait"
      echo "    push gate: cleared after ${PUSH_GATE_WAITED}s" >&2
    fi
  fi
fi

# ---------------------------------------------------------------------------
# Step 16: Push
# ---------------------------------------------------------------------------
echo "==> Step 16: Push" >&2

if [[ "$SKIP_PUSH" == "true" ]]; then
  PUSH_STATUS="skipped"
  PUSH_DETAIL="--skip-push flag"
  echo "    skipped (--skip-push)" >&2
elif [[ "$DRY_RUN" == "true" ]]; then
  PUSH_STATUS="skipped"
  PUSH_DETAIL="dry-run"
  echo "    skipped (dry-run)" >&2
elif [[ "$DEFER_PUSH" == "true" ]]; then
  PUSH_STATUS="deferred"
  PUSH_DETAIL="CI busy — push deferred to next session-close"
  echo "    deferred (CI busy, work stays in local main)" >&2
else
  # Push main branch
  PUSH_OUT=$(git -C "$GIT_WORK_DIR" push origin main 2>&1) || PUSH_EXIT=$?
  PUSH_EXIT=${PUSH_EXIT:-0}

  if [[ "$PUSH_EXIT" -eq 0 ]]; then
    PUSH_STATUS="ok"
    PUSH_DETAIL="pushed origin main"
    echo "    push ok" >&2

    # Push tag if we have one
    if [[ -n "$VERSION_TAG" ]]; then
      if git -C "$GIT_WORK_DIR" push origin "$VERSION_TAG" 2>/dev/null; then
        TAG_PUSHED=true
        echo "    pushed tag $VERSION_TAG" >&2
      else
        TAG_PUSHED=false
        echo "    tag push failed (non-blocking)" >&2
      fi
    fi
  else
    PUSH_STATUS="failed"
    PUSH_DETAIL="$PUSH_OUT"
    echo "    push FAILED: $PUSH_OUT" >&2
  fi
fi

# ---------------------------------------------------------------------------
# Step 16a: Pipeline watch
# ---------------------------------------------------------------------------
echo "==> Step 16a: Pipeline watch" >&2

if [[ "$SKIP_PIPELINE" == "true" ]]; then
  PIPELINE_STATUS="skipped_flag"
  echo "    skipped (--skip-pipeline)" >&2
elif [[ "$PUSH_STATUS" == "deferred" ]]; then
  PIPELINE_STATUS="skipped_push_deferred"
  echo "    skipped (push deferred to next session-close)" >&2
elif [[ "$PUSH_STATUS" != "ok" ]]; then
  PIPELINE_STATUS="skipped_push_failed"
  echo "    skipped (push was not ok: $PUSH_STATUS)" >&2
elif [[ ! -f "$HANDLERS_DIR/pipeline-watch.sh" ]]; then
  PIPELINE_STATUS="skipped_no_handler"
  echo "    skipped (pipeline-watch.sh not found)" >&2
else
  PUSH_SHA="$(git -C "$GIT_WORK_DIR" rev-parse HEAD 2>/dev/null || echo "")"
  PW_OUT=$(bash "$HANDLERS_DIR/pipeline-watch.sh" \
    --repo-dir "$GIT_WORK_DIR" \
    --sha "$PUSH_SHA" \
    "${DRY_RUN_ARGS[@]}" 2>&1) || PW_EXIT=$?
  PW_EXIT=${PW_EXIT:-0}

  PIPELINE_STATUS=$(echo "$PW_OUT" | grep '^PIPELINE_STATUS=' | cut -d= -f2 || echo "unknown")
  PIPELINE_RUN_URL=$(echo "$PW_OUT" | grep '^PIPELINE_RUN_URL=' | cut -d= -f2 || echo "")
  echo "    pipeline status: $PIPELINE_STATUS" >&2

  if [[ "$PW_EXIT" -ne 0 ]]; then
    PIPELINE_ERROR=$(echo "$PW_OUT" | grep '^PIPELINE_ERROR=' | cut -d= -f2 || echo "")
    # Pipeline fail means beads stay in_progress; we return partial JSON exit 0
    # so the caller can surface the failure and not close beads
    jq -cn \
      --argjson killed "$(printf '%s\n' "${KILL_PROCS_KILLED[@]+"${KILL_PROCS_KILLED[@]}"}" | jq -R . | jq -s . || echo '[]')" \
      --argjson msc_committed "$(printf '%s\n' "${MAIN_SCAN_COMMITTED_FILES[@]+"${MAIN_SCAN_COMMITTED_FILES[@]}"}" | jq -R . | jq -s . || echo '[]')" \
      --argjson msc_advisory "$(printf '%s\n' "${MAIN_SCAN_ADVISORY_FILES[@]+"${MAIN_SCAN_ADVISORY_FILES[@]}"}" | jq -R . | jq -s . || echo '[]')" \
      --arg kps "$KILL_PROCS_STATUS" \
      --arg sms "$SECOND_MERGE_STATUS" --arg smd "$SECOND_MERGE_DETAIL" \
      --arg mscs "$MAIN_SCAN_STATUS" \
      --arg mfs "$MERGE_FEATURE_STATUS" --arg mfd "$MERGE_FEATURE_DETAIL" \
      --arg vs "$VERSION_STATUS" --arg vt "$VERSION_TAG" --arg vv "$VERSION_VER" \
      --arg pgs "$PUSH_GATE_STATUS" --arg pgd "$PUSH_GATE_DETAIL" --argjson pgw "$PUSH_GATE_WAITED" \
      --arg ps "$PUSH_STATUS" --arg pd "$PUSH_DETAIL" \
      --arg pls "$PIPELINE_STATUS" --arg plu "$PIPELINE_RUN_URL" --arg ple "$PIPELINE_ERROR" \
      '{
        kill_procs: {status:$kps, killed:$killed},
        second_merge: {status:$sms, detail:$smd},
        main_repo_scan: {status:$mscs, committed_files:$msc_committed, advisory_files:$msc_advisory},
        merge_feature: {status:$mfs, detail:$mfd},
        version: {status:$vs, tag:$vt, version:$vv},
        push_gate: {status:$pgs, detail:$pgd, waited_seconds:$pgw},
        push: {status:$ps, detail:$pd},
        pipeline: {status:$pls, run_url:$plu, error:$ple},
        plugin_cache: {status:"not_attempted", detail:"pipeline failed — beads NOT closed"}
      }'
    exit 0
  fi
fi

# ---------------------------------------------------------------------------
# Step 16c: Sync plugin cache
# ---------------------------------------------------------------------------
echo "==> Step 16c: Sync plugin cache" >&2

if [[ "$PUSH_STATUS" == "deferred" ]]; then
  PLUGIN_CACHE_STATUS="skipped"
  PLUGIN_CACHE_DETAIL="push deferred (cache will sync after next push)"
  echo "    skipped (push deferred)" >&2
elif [[ "$PUSH_STATUS" != "ok" ]]; then
  PLUGIN_CACHE_STATUS="skipped"
  PLUGIN_CACHE_DETAIL="push was not ok"
  echo "    skipped (push not ok)" >&2
elif [[ "$DRY_RUN" == "true" ]]; then
  PLUGIN_CACHE_STATUS="skipped"
  PLUGIN_CACHE_DETAIL="dry-run"
  echo "    skipped (dry-run)" >&2
elif [[ ! -f "$HANDLERS_DIR/sync-plugin-cache.sh" ]]; then
  PLUGIN_CACHE_STATUS="skipped"
  PLUGIN_CACHE_DETAIL="sync-plugin-cache.sh not found"
  echo "    skipped (handler missing)" >&2
else
  PC_OUT=$(bash "$HANDLERS_DIR/sync-plugin-cache.sh" "$REPO_ROOT" 2>&1) || true
  echo "$PC_OUT" | head -10 >&2
  if echo "$PC_OUT" | grep -q "✔\|Successfully\|Updated\|already at"; then
    PLUGIN_CACHE_STATUS="ok"
    PLUGIN_CACHE_DETAIL="cache synced"
  elif echo "$PC_OUT" | grep -q "skipping\|no plugin\|not found"; then
    PLUGIN_CACHE_STATUS="skipped"
    PLUGIN_CACHE_DETAIL="$(echo "$PC_OUT" | head -1)"
  else
    PLUGIN_CACHE_STATUS="ok"
    PLUGIN_CACHE_DETAIL="$(echo "$PC_OUT" | head -1)"
  fi
fi

# ---------------------------------------------------------------------------
# Emit JSON
# ---------------------------------------------------------------------------
echo "==> Emitting JSON result" >&2

to_json_array() {
  local arr=("$@")
  if [[ ${#arr[@]} -eq 0 ]]; then
    echo "[]"
  else
    printf '%s\n' "${arr[@]}" | jq -R . | jq -s .
  fi
}

KILLED_JSON=$(to_json_array "${KILL_PROCS_KILLED[@]+"${KILL_PROCS_KILLED[@]}"}")
MSC_COMMITTED_JSON=$(to_json_array "${MAIN_SCAN_COMMITTED_FILES[@]+"${MAIN_SCAN_COMMITTED_FILES[@]}"}")
MSC_ADVISORY_JSON=$(to_json_array "${MAIN_SCAN_ADVISORY_FILES[@]+"${MAIN_SCAN_ADVISORY_FILES[@]}"}")

jq -cn \
  --arg kps "$KILL_PROCS_STATUS" \
  --argjson killed "$KILLED_JSON" \
  --arg sms "$SECOND_MERGE_STATUS" --arg smd "$SECOND_MERGE_DETAIL" \
  --arg mscs "$MAIN_SCAN_STATUS" \
  --argjson msc_committed "$MSC_COMMITTED_JSON" \
  --argjson msc_advisory "$MSC_ADVISORY_JSON" \
  --arg mfs "$MERGE_FEATURE_STATUS" --arg mfd "$MERGE_FEATURE_DETAIL" \
  --arg vs "$VERSION_STATUS" --arg vt "$VERSION_TAG" --arg vv "$VERSION_VER" \
  --arg pgs "$PUSH_GATE_STATUS" --arg pgd "$PUSH_GATE_DETAIL" --argjson pgw "$PUSH_GATE_WAITED" \
  --arg ps "$PUSH_STATUS" --arg pd "$PUSH_DETAIL" \
  --argjson tp "$TAG_PUSHED" \
  --arg pls "$PIPELINE_STATUS" --arg plu "$PIPELINE_RUN_URL" \
  --arg pcs "$PLUGIN_CACHE_STATUS" --arg pcd "$PLUGIN_CACHE_DETAIL" \
  '{
    kill_procs: {status: $kps, killed: $killed},
    second_merge: {status: $sms, detail: $smd},
    main_repo_scan: {status: $mscs, committed_files: $msc_committed, advisory_files: $msc_advisory},
    merge_feature: {status: $mfs, detail: $mfd},
    version: {status: $vs, tag: $vt, version: $vv},
    push_gate: {status: $pgs, detail: $pgd, waited_seconds: $pgw},
    push: {status: $ps, detail: $pd, tag_pushed: $tp},
    pipeline: {status: $pls, run_url: $plu},
    plugin_cache: {status: $pcs, detail: $pcd}
  }'
