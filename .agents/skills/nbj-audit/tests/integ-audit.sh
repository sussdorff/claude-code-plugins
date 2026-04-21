#!/bin/bash
# integ-audit.sh — Integration tests for nbj-audit.sh
# Verifies harness mode, project mode, and delta tracking

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
AUDIT_SCRIPT="$SKILL_DIR/scripts/nbj-audit.sh"

PASS=0
FAIL=0

pass() { echo "PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $1"; FAIL=$((FAIL + 1)); }

# Shared temp dirs — created up-front so a single trap can clean all of them
TMPDIR_DELTA="$(mktemp -d)"
TMPDIR_PROJ="$(mktemp -d)"
TMPDIR_HARNESS="$(mktemp -d)"
cleanup() { rm -rf "$TMPDIR_DELTA" "$TMPDIR_PROJ" "$TMPDIR_HARNESS"; }
trap cleanup EXIT

# ── Test 1: Script exists and is executable ──────────────────────────────────
if [ -f "$AUDIT_SCRIPT" ]; then
    pass "nbj-audit.sh exists"
else
    fail "scripts/nbj-audit.sh not found at $AUDIT_SCRIPT"
    exit 1
fi

# ── Test 2: Script exits 0 on valid input ────────────────────────────────────
CLAUDE_REPO="$(cd "$SKILL_DIR/../../../" && pwd)"
OUTPUT="$("$AUDIT_SCRIPT" "$CLAUDE_REPO" 2>&1)"
EXIT_CODE=$?

if [ "$EXIT_CODE" -eq 0 ]; then
    pass "script exits 0"
else
    fail "nbj-audit.sh exited with code $EXIT_CODE"
    echo "Output:"
    echo "$OUTPUT"
    exit 1
fi

# ── Test 3: Mode detection — harness mode ────────────────────────────────────
if echo "$OUTPUT" | grep -q "mode=harness"; then
    pass "harness mode detected"
else
    fail "expected 'mode=harness' in output for claude repo"
    echo "Actual output snippet:"
    echo "$OUTPUT" | head -20
    exit 1
fi

# ── Test 4: Skills count reported ────────────────────────────────────────────
if echo "$OUTPUT" | grep -qE "skills_count=[0-9]+"; then
    pass "skills count reported"
else
    fail "expected 'skills_count=N' in output"
    echo "Actual output snippet:"
    echo "$OUTPUT" | head -30
    exit 1
fi

# ── Test 5: All 12 primitives listed ─────────────────────────────────────────
PRIMITIVE_COUNT=$(echo "$OUTPUT" | grep -cE "^PRIMITIVE:" || true)
if [ "$PRIMITIVE_COUNT" -ge 12 ]; then
    pass "12 primitives listed"
else
    fail "expected 12 PRIMITIVE: lines, got $PRIMITIVE_COUNT"
    echo "Actual output:"
    echo "$OUTPUT"
    exit 1
fi

# ── Test 6: Each primitive has status field ───────────────────────────────────
MISSING_STATUS=$(echo "$OUTPUT" | grep "^PRIMITIVE:" | grep -vE "status=(present|partial|missing)" || true)
if [ -z "$MISSING_STATUS" ]; then
    pass "all primitives have status"
else
    fail "some primitives missing status field: $MISSING_STATUS"
    exit 1
fi

# ── Test 6b: TIMESTAMP line present ─────────────────────────────────────────
if echo "$OUTPUT" | grep -qE "^TIMESTAMP: [0-9]{4}-[0-9]{2}-[0-9]{2}T"; then
    pass "TIMESTAMP line present"
else
    fail "expected TIMESTAMP: YYYY-MM-DDTHH:MM:SSZ line in output"
    echo "Actual output tail:"
    echo "$OUTPUT" | tail -5
    exit 1
fi

# ── Test 7: Delta tracking — history file detection ──────────────────────────
mkdir -p "$TMPDIR_DELTA/.beads"
cat > "$TMPDIR_DELTA/.beads/nbj-audit-history.json" <<'EOF'
{
  "runs": [
    {
      "timestamp": "2026-04-01T10:00:00Z",
      "primitives": {
        "1": "present",
        "2": "missing"
      }
    }
  ]
}
EOF

mkdir -p "$TMPDIR_DELTA/src"
touch "$TMPDIR_DELTA/src/routes.ts"
touch "$TMPDIR_DELTA/src/auth.ts"

DELTA_OUTPUT="$("$AUDIT_SCRIPT" "$TMPDIR_DELTA" 2>&1)"
DELTA_EXIT=$?

if [ "$DELTA_EXIT" -eq 0 ]; then
    pass "script exits 0 on project with history"
else
    fail "script exited $DELTA_EXIT on project with history"
    echo "$DELTA_OUTPUT"
fi

if echo "$DELTA_OUTPUT" | grep -qE "HISTORY:.*exists"; then
    pass "HISTORY: ... exists line present"
else
    fail "expected 'HISTORY: ... exists' in output"
    echo "Actual output:"
    echo "$DELTA_OUTPUT"
fi

if echo "$DELTA_OUTPUT" | grep -qE "HISTORY_LAST_RUN:"; then
    pass "HISTORY_LAST_RUN: line present"
else
    fail "expected 'HISTORY_LAST_RUN:' in output"
    echo "Actual output:"
    echo "$DELTA_OUTPUT"
fi

# ── Test 8: Project mode — 12 primitives for non-harness dir ─────────────────
mkdir -p "$TMPDIR_PROJ/src"
touch "$TMPDIR_PROJ/src/routes.ts"
touch "$TMPDIR_PROJ/src/auth.middleware.ts"
touch "$TMPDIR_PROJ/src/user.test.ts"

PROJ_OUTPUT="$("$AUDIT_SCRIPT" "$TMPDIR_PROJ" 2>&1)"
PROJ_EXIT=$?

if [ "$PROJ_EXIT" -eq 0 ]; then
    pass "script exits 0 in project mode"
else
    fail "script exited $PROJ_EXIT in project mode"
    echo "$PROJ_OUTPUT"
fi

if echo "$PROJ_OUTPUT" | grep -q "mode=project"; then
    pass "project mode detected"
else
    fail "expected 'mode=project' in output for non-harness dir"
    echo "Actual output snippet:"
    echo "$PROJ_OUTPUT" | head -10
fi

PROJ_PRIM_COUNT=$(echo "$PROJ_OUTPUT" | grep -cE "^PRIMITIVE:" || true)
if [ "$PROJ_PRIM_COUNT" -ge 12 ]; then
    pass "project mode emits 12 PRIMITIVE lines"
else
    fail "project mode: expected 12 PRIMITIVE lines, got $PROJ_PRIM_COUNT"
    echo "Actual output:"
    echo "$PROJ_OUTPUT"
fi

# ── Test 9: Delta tracking — history detection in harness mode ───────────────
mkdir -p "$TMPDIR_HARNESS/malte/skills"
mkdir -p "$TMPDIR_HARNESS/malte/agents"
mkdir -p "$TMPDIR_HARNESS/.beads"
cat > "$TMPDIR_HARNESS/.beads/nbj-audit-history.json" <<'EOF'
{
  "runs": [
    {
      "timestamp": "2026-04-01T10:00:00Z",
      "primitives": {
        "1": "partial",
        "2": "missing"
      }
    }
  ]
}
EOF

HARNESS_HISTORY_OUTPUT="$("$AUDIT_SCRIPT" "$TMPDIR_HARNESS" 2>&1)"
HARNESS_HISTORY_EXIT=$?

if [ "$HARNESS_HISTORY_EXIT" -eq 0 ]; then
    pass "script exits 0 on harness with history"
else
    fail "script exited $HARNESS_HISTORY_EXIT on harness with history"
    echo "$HARNESS_HISTORY_OUTPUT"
fi

if echo "$HARNESS_HISTORY_OUTPUT" | grep -qE "HISTORY:.*exists"; then
    pass "harness mode: HISTORY: ... exists line present"
else
    fail "harness mode: expected 'HISTORY: ... exists' in output"
    echo "Actual output:"
    echo "$HARNESS_HISTORY_OUTPUT"
fi

if echo "$HARNESS_HISTORY_OUTPUT" | grep -qE "HISTORY_LAST_RUN:"; then
    pass "harness mode: HISTORY_LAST_RUN: line present"
else
    fail "harness mode: expected 'HISTORY_LAST_RUN:' in output"
    echo "Actual output:"
    echo "$HARNESS_HISTORY_OUTPUT"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
echo "All tests passed."
