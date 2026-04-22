#!/usr/bin/env bash
# ci-monitor.sh — Watch the CI pipeline for a specific pushed commit.
#
# Thin wrapper around pipeline-watch.sh that resolves the handlers dir
# relative to itself (no external path knowledge required).
#
# Usage: ci-monitor.sh --repo-dir <dir> --sha <sha> [--dry-run]
#
# Outputs one verdict line on stdout:
#   PIPELINE: PASSED (run: <url>)
#   PIPELINE: FAILED (run: <url>, error: <detail>)
#   PIPELINE: FAILED (error: no_run_registered — workflow exists but no run started)
#   PIPELINE: SKIPPED (<reason>)
#
# Exit codes:
#   0 — passed or skipped (caller may proceed)
#   1 — failed (caller must not close beads)

set -uo pipefail

REPO_DIR=""
SHA=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-dir) REPO_DIR="${2:-}"; shift 2 ;;
    --sha)      SHA="${2:-}";      shift 2 ;;
    --dry-run)  DRY_RUN=true;      shift ;;
    *) shift ;;
  esac
done

if [[ -z "$REPO_DIR" || -z "$SHA" ]]; then
  echo "PIPELINE: FAILED (error: missing --repo-dir or --sha)"
  exit 1
fi

HANDLERS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f "$HANDLERS_DIR/pipeline-watch.sh" ]]; then
  echo "PIPELINE: SKIPPED (pipeline-watch.sh not found in $HANDLERS_DIR)"
  exit 0
fi

PW_OUT=$(bash "$HANDLERS_DIR/pipeline-watch.sh" \
  --repo-dir "$REPO_DIR" \
  --sha "$SHA" \
  ${DRY_RUN:+--dry-run} 2>/dev/null)
PW_EXIT=${PIPESTATUS[0]:-$?}

PIPELINE_STATUS=$(echo "$PW_OUT" | grep '^PIPELINE_STATUS=' | cut -d= -f2)
PIPELINE_RUN_URL=$(echo "$PW_OUT" | grep '^PIPELINE_RUN_URL=' | cut -d= -f2 || echo "")
PIPELINE_ERROR=$(echo "$PW_OUT" | grep '^PIPELINE_ERROR=' | cut -d= -f2 || echo "")

case "$PIPELINE_STATUS" in
  passed)
    echo "PIPELINE: PASSED${PIPELINE_RUN_URL:+ (run: $PIPELINE_RUN_URL)}"
    exit 0
    ;;
  failed)
    if [[ "$PIPELINE_ERROR" == "no_run_registered" ]]; then
      echo "PIPELINE: FAILED (error: no_run_registered — workflow exists but no run started)"
    else
      echo "PIPELINE: FAILED${PIPELINE_RUN_URL:+ (run: $PIPELINE_RUN_URL)}${PIPELINE_ERROR:+, error: $PIPELINE_ERROR}"
    fi
    exit 1
    ;;
  skipped_dry_run)
    echo "PIPELINE: SKIPPED (dry-run)"
    exit 0
    ;;
  skipped_*)
    REASON="${PIPELINE_STATUS#skipped_}"
    echo "PIPELINE: SKIPPED ($REASON)"
    exit 0
    ;;
  *)
    echo "PIPELINE: SKIPPED (unknown status: ${PIPELINE_STATUS:-empty})"
    exit 0
    ;;
esac
