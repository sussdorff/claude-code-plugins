#!/usr/bin/env bash
# Test suite for scripts/fetch-latest.sh
# RED phase: run this before the script exists to confirm failure, then again after (GREEN)
#
# Usage: bash tests/test-fetch-latest.sh

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$SKILL_DIR/scripts/fetch-latest.sh"

PASS=0
FAIL=0
SKIP=0

pass() { echo "  PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }
skip() { echo "  SKIP: $1"; SKIP=$((SKIP+1)); }

# ── Test 1: Script exists and is executable ──────────────────────────────────

echo "=== Test: script exists ==="
if [[ -f "$SCRIPT" ]]; then
  pass "fetch-latest.sh exists at $SCRIPT"
else
  fail "fetch-latest.sh NOT FOUND at $SCRIPT"
fi

# Bail early — remaining tests require the script
if [[ ! -f "$SCRIPT" ]]; then
  echo ""
  echo "RESULT: ${PASS} passed, ${FAIL} failed, ${SKIP} skipped"
  echo "Stopping: script missing. Create scripts/fetch-latest.sh and rerun."
  exit 1
fi

# ── Test 2: Script runs without error ────────────────────────────────────────

echo ""
echo "=== Test: script exits 0 ==="
if bash "$SCRIPT" > /dev/null 2>&1; then
  pass "script exits 0"
else
  fail "script exited non-zero (exit $?)"
fi

# ── Test 3: Output contains required keys ────────────────────────────────────

echo ""
echo "=== Test: required output keys ==="
OUTPUT="$(bash "$SCRIPT" 2>&1)" || true

check_key() {
  local key="$1"
  if echo "$OUTPUT" | grep -q "^${key}="; then
    pass "output contains ${key}="
  else
    fail "output MISSING ${key}= (got: $(echo "$OUTPUT" | head -5))"
  fi
}

check_key "BASELINE_VERSION"
check_key "LATEST_VERSION"
check_key "STATUS"

# ── Test 4: STATUS is one of valid values ─────────────────────────────────────

echo ""
echo "=== Test: STATUS value is valid ==="
STATUS_LINE="$(echo "$OUTPUT" | grep '^STATUS=' || echo 'STATUS=')"
STATUS_VAL="${STATUS_LINE#STATUS=}"

if [[ "$STATUS_VAL" == "current" || "$STATUS_VAL" == "outdated" ]]; then
  pass "STATUS='$STATUS_VAL' is valid"
else
  fail "STATUS='$STATUS_VAL' is not 'current' or 'outdated'"
fi

# ── Test 5: BASELINE_VERSION matches semver-like pattern ─────────────────────

echo ""
echo "=== Test: BASELINE_VERSION format ==="
BASELINE_LINE="$(echo "$OUTPUT" | grep '^BASELINE_VERSION=' || echo 'BASELINE_VERSION=')"
BASELINE_VAL="${BASELINE_LINE#BASELINE_VERSION=}"

if [[ "$BASELINE_VAL" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  pass "BASELINE_VERSION='$BASELINE_VAL' matches N.N.N"
else
  fail "BASELINE_VERSION='$BASELINE_VAL' does not match N.N.N"
fi

# ── Test 6: LATEST_VERSION matches semver-like pattern ───────────────────────

echo ""
echo "=== Test: LATEST_VERSION format ==="
LATEST_LINE="$(echo "$OUTPUT" | grep '^LATEST_VERSION=' || echo 'LATEST_VERSION=')"
LATEST_VAL="${LATEST_LINE#LATEST_VERSION=}"

if [[ "$LATEST_VAL" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  pass "LATEST_VERSION='$LATEST_VAL' matches N.N.N"
else
  fail "LATEST_VERSION='$LATEST_VAL' does not match N.N.N"
fi

# ── Test 7: When outdated, NEW_PROMPT_FILE is set and file exists ─────────────

echo ""
echo "=== Test: NEW_PROMPT_FILE (when outdated) ==="
if [[ "$STATUS_VAL" == "outdated" ]]; then
  NPFILE_LINE="$(echo "$OUTPUT" | grep '^NEW_PROMPT_FILE=' || echo '')"
  if [[ -n "$NPFILE_LINE" ]]; then
    NPFILE_VAL="${NPFILE_LINE#NEW_PROMPT_FILE=}"
    if [[ -f "$NPFILE_VAL" ]]; then
      pass "NEW_PROMPT_FILE='$NPFILE_VAL' exists"
    else
      fail "NEW_PROMPT_FILE='$NPFILE_VAL' does NOT exist on disk"
    fi
  else
    fail "STATUS=outdated but NEW_PROMPT_FILE not in output"
  fi
else
  skip "STATUS=current — NEW_PROMPT_FILE not expected"
fi

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "================================"
echo "RESULT: ${PASS} passed, ${FAIL} failed, ${SKIP} skipped"
echo "================================"

[[ $FAIL -eq 0 ]]
