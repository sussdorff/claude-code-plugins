#!/usr/bin/env bash
# phase-b-prepare.sh - Phase B preparation batch handler
#
# Consolidates Steps 1, 2, 3, 4, 5, 7, 9 from session-close into a single
# script that emits one JSON document. Replaces ~7 individual handler calls
# with one tool use, targeting <=20 total tool uses per session-close.
#
# Steps executed (in order):
#   1: First merge from main (merge-from-main.sh)
#   2: Plan cleanup (malte/plans/ bead-ID-named files)
#   3: Git status/diff capture
#   4: Bun audit              (skip with --skip-audit)
#   5: Code simplification advisory (skip with --skip-simplify)
#   7: Changelog generation (git-cliff, stages CHANGELOG.md for step 6 commit)
#   9: Docs check advisory (docs-check.sh)
#
# IMPORTANT: Step 7 stages CHANGELOG.md but does NOT create a separate commit.
# The caller (session-close Step 6) should include CHANGELOG.md in the
# conventional commit when changelog.status == "updated".
#
# Usage:
#   phase-b-prepare.sh [--dry-run] [--skip-audit] [--skip-simplify]
#
# Emits a single JSON document on stdout; stderr for human-readable progress.
#
# Exit codes:
#   0 - all steps ok (or partial failure with actionable JSON)
#   2 - merge conflict (caller MUST stop session-close)
#   1 - internal/unparseable error
#
# Idempotency: safe to re-run. Merge is no-op if already current. Changelog
# is no-op if no new commits since last tag. Plan cleanup is no-op if files
# already deleted.
#
# Schema: phase-b-prepare.schema.json

set -uo pipefail

# ---------------------------------------------------------------------------
# Flag parsing
# ---------------------------------------------------------------------------
DRY_RUN=false
SKIP_AUDIT=false
SKIP_SIMPLIFY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)       DRY_RUN=true;       shift ;;
    --skip-audit)    SKIP_AUDIT=true;    shift ;;
    --skip-simplify) SKIP_SIMPLIFY=true; shift ;;
    *) shift ;;
  esac
done

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"
if [[ -z "$REPO_ROOT" ]]; then
  echo '{"error":"not_in_git_repo"}' >&1
  exit 1
fi

HANDLERS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLANS_DIR="$REPO_ROOT/malte/plans"

# ---------------------------------------------------------------------------
# Result accumulators (JSON-safe via jq at the end)
# ---------------------------------------------------------------------------
FIRST_MERGE_STATUS="not_attempted"
FIRST_MERGE_DETAIL=""

PLAN_DELETED=()
PLAN_KEPT=()

GIT_STAGED=()
GIT_UNSTAGED=()
GIT_UNTRACKED=()

BUN_AUDIT_STATUS="skipped"
BUN_AUDIT_VULNS=()

SIMPLIFY_STATUS="skipped"
SIMPLIFY_CHANGED=0

CHANGELOG_STATUS="skipped"
CHANGELOG_COMMIT_MADE=false

DOCS_GAPS=()

# ---------------------------------------------------------------------------
# Step 1: First merge from main
# ---------------------------------------------------------------------------
echo "==> Step 1: First merge from main" >&2

MERGE_OUT=$(bash "$HANDLERS_DIR/merge-from-main.sh" \
  ${DRY_RUN:+--dry-run} --label "first" 2>&1) || MERGE_EXIT=$?
MERGE_EXIT=${MERGE_EXIT:-0}

MERGE_STATUS_RAW=$(echo "$MERGE_OUT" | grep '^MERGE_FROM_MAIN_STATUS=' | cut -d= -f2)

case "$MERGE_STATUS_RAW" in
  success)          FIRST_MERGE_STATUS="ok"; FIRST_MERGE_DETAIL="merged origin/main" ;;
  skipped_on_main)  FIRST_MERGE_STATUS="skipped"; FIRST_MERGE_DETAIL="branch is main" ;;
  skipped_dry_run)  FIRST_MERGE_STATUS="skipped"; FIRST_MERGE_DETAIL="dry-run" ;;
  conflict)
    FIRST_MERGE_STATUS="conflict"
    FIRST_MERGE_DETAIL="merge conflict — resolve and re-run"
    # Emit minimal JSON so caller has something to parse, then exit 2
    jq -cn \
      --arg ms "$FIRST_MERGE_STATUS" \
      --arg md "$FIRST_MERGE_DETAIL" \
      '{
        first_merge: {status:$ms, detail:$md},
        plan_cleanup: {deleted:[], kept:[]},
        git_state: {staged:[], unstaged:[], untracked:[]},
        bun_audit: {status:"not_attempted", vulns:[]},
        simplify: {status:"not_attempted", changed_code_files:0},
        changelog: {status:"not_attempted", commit_made:false},
        docs_check: {gaps:[]}
      }'
    exit 2
    ;;
  error_fetch)
    FIRST_MERGE_STATUS="failed"
    FIRST_MERGE_DETAIL="git fetch origin main failed"
    ;;
  *)
    FIRST_MERGE_STATUS="unknown"
    FIRST_MERGE_DETAIL="$MERGE_STATUS_RAW"
    ;;
esac
echo "    merge status: $FIRST_MERGE_STATUS" >&2

# ---------------------------------------------------------------------------
# Step 2: Plan cleanup
# ---------------------------------------------------------------------------
echo "==> Step 2: Plan cleanup" >&2

if [[ -d "$PLANS_DIR" ]]; then
  while IFS= read -r -d '' plan_file; do
    base=$(basename "$plan_file")
    # Bead ID pattern: one or more lowercase letters, dash, 3+ alphanumeric chars
    if [[ "$base" =~ ^[a-z]+-[a-z0-9]{3,}$ ]]; then
      bead_status=$(bd show "$base" --json 2>/dev/null | python3 -c \
        "import sys,json; d=json.load(sys.stdin); print(d[0].get('status','unknown'))" \
        2>/dev/null || echo "unknown")
      if [[ "$bead_status" == "closed" || "$bead_status" == "unknown" ]]; then
        if [[ "$DRY_RUN" == "false" ]]; then
          rm -f "$plan_file"
          echo "    deleted plan: $base" >&2
        else
          echo "    [dry-run] would delete: $base" >&2
        fi
        PLAN_DELETED+=("$base")
      else
        PLAN_KEPT+=("$base")
        echo "    kept plan: $base (status: $bead_status)" >&2
      fi
    fi
  done < <(find "$PLANS_DIR" -maxdepth 1 -type f -print0 2>/dev/null)
else
  echo "    no plans dir, skipping" >&2
fi

# ---------------------------------------------------------------------------
# Step 3: Git status/diff capture
# ---------------------------------------------------------------------------
echo "==> Step 3: Git status capture" >&2

while IFS= read -r line; do
  code="${line:0:2}"
  file="${line:3}"
  [[ -z "$file" ]] && continue
  index_code="${code:0:1}"
  worktree_code="${code:1:1}"
  if [[ "$index_code" != " " && "$index_code" != "?" ]]; then
    GIT_STAGED+=("$file")
  fi
  if [[ "$worktree_code" == "M" || "$worktree_code" == "D" ]]; then
    GIT_UNSTAGED+=("$file")
  fi
  if [[ "$index_code" == "?" && "$worktree_code" == "?" ]]; then
    GIT_UNTRACKED+=("$file")
  fi
done < <(git -C "$REPO_ROOT" status --porcelain 2>/dev/null)

echo "    staged: ${#GIT_STAGED[@]}, unstaged: ${#GIT_UNSTAGED[@]}, untracked: ${#GIT_UNTRACKED[@]}" >&2

# ---------------------------------------------------------------------------
# Step 4: Bun audit
# ---------------------------------------------------------------------------
echo "==> Step 4: Bun audit" >&2

if [[ "$SKIP_AUDIT" == "true" ]]; then
  BUN_AUDIT_STATUS="skipped"
  echo "    skipped (--skip-audit)" >&2
elif [[ "$DRY_RUN" == "true" ]]; then
  BUN_AUDIT_STATUS="skipped"
  echo "    skipped (dry-run)" >&2
elif ! command -v bun &>/dev/null; then
  BUN_AUDIT_STATUS="skipped"
  echo "    skipped (bun not installed)" >&2
else
  AUDIT_OUT=$(cd "$REPO_ROOT" && bun audit --severity high 2>/dev/null || true)
  FRONTEND_OUT=""
  if [[ -d "$REPO_ROOT/frontend" ]]; then
    FRONTEND_OUT=$(cd "$REPO_ROOT/frontend" && bun audit --severity high 2>/dev/null || true)
  fi
  ALL_AUDIT="$AUDIT_OUT $FRONTEND_OUT"

  if echo "$ALL_AUDIT" | grep -qi "critical"; then
    BUN_AUDIT_STATUS="critical"
    while IFS= read -r vuln_line; do
      [[ -n "$vuln_line" ]] && BUN_AUDIT_VULNS+=("$vuln_line")
    done < <(echo "$ALL_AUDIT" | grep -i "critical" | head -10)
  elif echo "$ALL_AUDIT" | grep -qi "high\|moderate"; then
    BUN_AUDIT_STATUS="high"
    while IFS= read -r vuln_line; do
      [[ -n "$vuln_line" ]] && BUN_AUDIT_VULNS+=("$vuln_line")
    done < <(echo "$ALL_AUDIT" | grep -iE "high|moderate" | head -10)
  else
    BUN_AUDIT_STATUS="ok"
  fi
  echo "    audit status: $BUN_AUDIT_STATUS" >&2
fi

# ---------------------------------------------------------------------------
# Step 5: Code simplification advisory
# ---------------------------------------------------------------------------
echo "==> Step 5: Code simplification advisory" >&2

if [[ "$SKIP_SIMPLIFY" == "true" ]]; then
  SIMPLIFY_STATUS="skipped"
  echo "    skipped (--skip-simplify)" >&2
else
  LATEST_TAG=$(git -C "$REPO_ROOT" describe --tags --abbrev=0 2>/dev/null || echo "")
  if [[ -n "$LATEST_TAG" ]]; then
    RANGE="${LATEST_TAG}..HEAD"
  else
    RANGE="HEAD~10..HEAD"
  fi
  CODE_COUNT=$(git -C "$REPO_ROOT" diff --name-only "$RANGE" 2>/dev/null \
    | grep -cEvE '\.(md|txt|json|yml|yaml|toml|lock)$' || true)
  SIMPLIFY_CHANGED="$CODE_COUNT"
  if [[ "$CODE_COUNT" -gt 0 ]]; then
    SIMPLIFY_STATUS="advisory"
    echo "    advisory: $CODE_COUNT code files changed since last tag" >&2
  else
    SIMPLIFY_STATUS="ok"
    echo "    no code changes to simplify" >&2
  fi
fi

# ---------------------------------------------------------------------------
# Step 7: Changelog generation
# ---------------------------------------------------------------------------
echo "==> Step 7: Changelog" >&2

if [[ "$DRY_RUN" == "true" ]]; then
  CHANGELOG_STATUS="skipped"
  echo "    skipped (dry-run)" >&2
elif ! command -v git-cliff &>/dev/null; then
  CHANGELOG_STATUS="skipped"
  echo "    skipped (git-cliff not installed)" >&2
elif [[ ! -f "$REPO_ROOT/cliff.toml" ]]; then
  CHANGELOG_STATUS="skipped"
  echo "    skipped (no cliff.toml)" >&2
else
  LATEST_TAG=$(git -C "$REPO_ROOT" describe --tags --abbrev=0 2>/dev/null || echo "")
  if [[ -n "$LATEST_TAG" ]]; then
    COMMIT_COUNT=$(git -C "$REPO_ROOT" log "${LATEST_TAG}..HEAD" --oneline 2>/dev/null | wc -l | tr -d ' ')
  else
    COMMIT_COUNT=$(git -C "$REPO_ROOT" log --oneline 2>/dev/null | wc -l | tr -d ' ')
  fi

  if [[ "$COMMIT_COUNT" -eq 0 ]]; then
    CHANGELOG_STATUS="no_change"
    echo "    no new commits for changelog" >&2
  else
    CHANGELOG_FILE="$REPO_ROOT/CHANGELOG.md"
    (cd "$REPO_ROOT" && git-cliff --config cliff.toml --output "$CHANGELOG_FILE" 2>/dev/null)
    if [[ -f "$CHANGELOG_FILE" ]]; then
      git -C "$REPO_ROOT" add "$CHANGELOG_FILE"
      CHANGELOG_STATUS="updated"
      CHANGELOG_COMMIT_MADE=false   # Staged only; caller commits in Step 6
      echo "    CHANGELOG.md updated and staged (include in Step 6 commit)" >&2
    else
      CHANGELOG_STATUS="no_change"
      echo "    git-cliff produced no output" >&2
    fi
  fi
fi

# ---------------------------------------------------------------------------
# Step 9: Docs check
# ---------------------------------------------------------------------------
echo "==> Step 9: Docs check" >&2

if [[ -f "$HANDLERS_DIR/docs-check.sh" ]]; then
  DOCS_OUT=$(bash "$HANDLERS_DIR/docs-check.sh" 2>/dev/null || true)
  while IFS= read -r gap_line; do
    [[ -n "$gap_line" ]] && DOCS_GAPS+=("$gap_line")
  done < <(echo "$DOCS_OUT" | grep -E '^\s+-' | sed 's/^\s*-\s*//')
  echo "    gaps found: ${#DOCS_GAPS[@]}" >&2
else
  echo "    docs-check.sh not found, skipping" >&2
fi

# ---------------------------------------------------------------------------
# Emit JSON
# ---------------------------------------------------------------------------
echo "==> Emitting JSON result" >&2

# Convert bash arrays to JSON arrays via jq
to_json_array() {
  local arr=("$@")
  if [[ ${#arr[@]} -eq 0 ]]; then
    echo "[]"
  else
    printf '%s\n' "${arr[@]}" | jq -R . | jq -s .
  fi
}

STAGED_JSON=$(to_json_array "${GIT_STAGED[@]+"${GIT_STAGED[@]}"}")
UNSTAGED_JSON=$(to_json_array "${GIT_UNSTAGED[@]+"${GIT_UNSTAGED[@]}"}")
UNTRACKED_JSON=$(to_json_array "${GIT_UNTRACKED[@]+"${GIT_UNTRACKED[@]}"}")
DELETED_JSON=$(to_json_array "${PLAN_DELETED[@]+"${PLAN_DELETED[@]}"}")
KEPT_JSON=$(to_json_array "${PLAN_KEPT[@]+"${PLAN_KEPT[@]}"}")
VULNS_JSON=$(to_json_array "${BUN_AUDIT_VULNS[@]+"${BUN_AUDIT_VULNS[@]}"}")
GAPS_JSON=$(to_json_array "${DOCS_GAPS[@]+"${DOCS_GAPS[@]}"}")

jq -cn \
  --arg fms "$FIRST_MERGE_STATUS" \
  --arg fmd "$FIRST_MERGE_DETAIL" \
  --argjson del "$DELETED_JSON" \
  --argjson kpt "$KEPT_JSON" \
  --argjson staged "$STAGED_JSON" \
  --argjson unstaged "$UNSTAGED_JSON" \
  --argjson untracked "$UNTRACKED_JSON" \
  --arg bas "$BUN_AUDIT_STATUS" \
  --argjson bavulns "$VULNS_JSON" \
  --arg simstatus "$SIMPLIFY_STATUS" \
  --argjson simchanged "$SIMPLIFY_CHANGED" \
  --arg cls "$CHANGELOG_STATUS" \
  --argjson clcommit "$CHANGELOG_COMMIT_MADE" \
  --argjson gaps "$GAPS_JSON" \
  '{
    first_merge: {status: $fms, detail: $fmd},
    plan_cleanup: {deleted: $del, kept: $kpt},
    git_state: {staged: $staged, unstaged: $unstaged, untracked: $untracked},
    bun_audit: {status: $bas, vulns: $bavulns},
    simplify: {status: $simstatus, changed_code_files: $simchanged},
    changelog: {status: $cls, commit_made: $clcommit},
    docs_check: {gaps: $gaps}
  }'
