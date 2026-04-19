#!/usr/bin/env bats
# Tests for wave-status.sh — covers bead-dropping bug and timezone bug.
#
# Stubs for external commands (cmux, bd) are injected via a bin/ directory
# prepended to PATH.

SCRIPT_DIR="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WAVE_STATUS="$REPO_ROOT/beads-workflow/skills/wave-orchestrator/scripts/wave-status.sh"
STUB_BIN="$SCRIPT_DIR/bin"

setup() {
  # Create stub bin directory
  mkdir -p "$STUB_BIN"

  # cmux stub: always returns a quiet idle shell prompt so status == "done"
  cat > "$STUB_BIN/cmux" <<'EOF'
#!/usr/bin/env bash
# Minimal stub: output an idle shell prompt
echo "$"
EOF
  chmod +x "$STUB_BIN/cmux"

  # bd stub: for any "show <id>", report CLOSED
  cat > "$STUB_BIN/bd" <<'EOF'
#!/usr/bin/env bash
# Usage: bd show <id>
# Report bead as CLOSED by default; honour BD_STUB_STATUS env var.
STATUS="${BD_STUB_STATUS:-CLOSED}"
echo "● P2 · $STATUS"
EOF
  chmod +x "$STUB_BIN/bd"

  export PATH="$STUB_BIN:$PATH"

  # Temporary directory for wave-config files used in each test
  TEST_TMPDIR=$(mktemp -d)
}

teardown() {
  rm -rf "$STUB_BIN" "$TEST_TMPDIR"
}

# ---------------------------------------------------------------------------
# Helper: write a wave-config.json with 2 beads
# ---------------------------------------------------------------------------
make_config() {
  local dispatch_time="$1"
  cat > "$TEST_TMPDIR/wave-config.json" <<EOF
{
  "dispatch_time": "$dispatch_time",
  "beads": [
    {"id": "test-aa1", "surface": "surface:1"},
    {"id": "test-bb2", "surface": "surface:2"}
  ]
}
EOF
  echo "$TEST_TMPDIR/wave-config.json"
}

# ---------------------------------------------------------------------------
# Bug 1: both beads must appear in the output array
# ---------------------------------------------------------------------------
@test "both beads appear in beads[] output for 2-bead config" {
  CONFIG=$(make_config "2026-04-19T10:00:00")
  run bash "$WAVE_STATUS" "$CONFIG"
  [ "$status" -eq 0 ]
  # Count the number of objects in the beads array
  BEAD_COUNT=$(echo "$output" | jq '.beads | length')
  [ "$BEAD_COUNT" -eq 2 ]
}

@test "bead ids are preserved correctly in output" {
  CONFIG=$(make_config "2026-04-19T10:00:00")
  run bash "$WAVE_STATUS" "$CONFIG"
  [ "$status" -eq 0 ]
  ID0=$(echo "$output" | jq -r '.beads[0].id')
  ID1=$(echo "$output" | jq -r '.beads[1].id')
  [ "$ID0" = "test-aa1" ]
  [ "$ID1" = "test-bb2" ]
}

# ---------------------------------------------------------------------------
# Bug 1: subshell must survive grep returning non-zero (no match scenario)
# The cmux stub below returns content that matches NO known status patterns,
# forcing grep calls throughout the subshell to return exit 1.
# With the old code (no set +euo pipefail in subshell), the subshell would
# die before writing its result file.
# ---------------------------------------------------------------------------
@test "beads are not dropped when grep returns non-zero inside subshell" {
  # Override cmux to return a string with no matching patterns at all
  cat > "$STUB_BIN/cmux" <<'EOF'
#!/usr/bin/env bash
echo "completely neutral output with no status keywords"
echo "another neutral line"
EOF
  chmod +x "$STUB_BIN/cmux"

  CONFIG=$(make_config "2026-04-19T10:00:00")
  run bash "$WAVE_STATUS" "$CONFIG"
  [ "$status" -eq 0 ]
  BEAD_COUNT=$(echo "$output" | jq '.beads | length')
  [ "$BEAD_COUNT" -eq 2 ]
}

# ---------------------------------------------------------------------------
# all_done logic
# ---------------------------------------------------------------------------
@test "all_done is true when all beads are closed" {
  export BD_STUB_STATUS="CLOSED"
  CONFIG=$(make_config "2026-04-19T10:00:00")
  run bash "$WAVE_STATUS" "$CONFIG"
  [ "$status" -eq 0 ]
  ALL_DONE=$(echo "$output" | jq '.all_done')
  [ "$ALL_DONE" = "true" ]
}

@test "all_done is false when at least one bead is not done" {
  # Make cmux return an in-progress screen (Claude active editing)
  cat > "$STUB_BIN/cmux" <<'EOF'
#!/usr/bin/env bash
echo "Edit tool running"
echo "Writing file..."
EOF
  chmod +x "$STUB_BIN/cmux"

  # bd returns OPEN (not closed)
  cat > "$STUB_BIN/bd" <<'EOF'
#!/usr/bin/env bash
echo "● P2 · OPEN"
EOF
  chmod +x "$STUB_BIN/bd"

  CONFIG=$(make_config "2026-04-19T10:00:00")
  run bash "$WAVE_STATUS" "$CONFIG"
  [ "$status" -eq 0 ]
  ALL_DONE=$(echo "$output" | jq '.all_done')
  [ "$ALL_DONE" = "false" ]
}

@test "all_done is false when only one of two beads is done" {
  # bd returns CLOSED for test-aa1 but OPEN for test-bb2.
  # cmux returns an active-editing screen for surface:2 so test-bb2 is not
  # detected as idle by _surface_is_idle (which would also set status=done).
  cat > "$STUB_BIN/cmux" <<'EOF'
#!/usr/bin/env bash
# Differentiate surfaces: surface:1 is idle, surface:2 is active
for arg in "$@"; do
  case "$arg" in
    surface:1) echo "$" ; exit 0 ;;
    surface:2) echo "Edit: Writing file..." ; echo "Bash: running tests" ; exit 0 ;;
  esac
done
echo "$"
EOF
  chmod +x "$STUB_BIN/cmux"

  cat > "$STUB_BIN/bd" <<'EOF'
#!/usr/bin/env bash
# bd show <id>
BEAD_ID="${3:-$2}"
case "$BEAD_ID" in
  test-aa1) echo "● P2 · CLOSED" ;;
  *)        echo "● P2 · OPEN"   ;;
esac
EOF
  chmod +x "$STUB_BIN/bd"

  CONFIG=$(make_config "2026-04-19T10:00:00")
  run bash "$WAVE_STATUS" "$CONFIG"
  [ "$status" -eq 0 ]
  ALL_DONE=$(echo "$output" | jq '.all_done')
  [ "$ALL_DONE" = "false" ]
}

# ---------------------------------------------------------------------------
# Bug 2: elapsed_minutes must use UTC, not local time
# ---------------------------------------------------------------------------
@test "elapsed_minutes is computed correctly using UTC" {
  # Dispatch exactly 60 minutes ago (UTC)
  DISPATCH_UTC=$(date -u -v-60M "+%Y-%m-%dT%H:%M:%S" 2>/dev/null \
    || date -u -d "60 minutes ago" "+%Y-%m-%dT%H:%M:%S" 2>/dev/null)

  CONFIG=$(make_config "$DISPATCH_UTC")
  run bash "$WAVE_STATUS" "$CONFIG"
  [ "$status" -eq 0 ]
  ELAPSED=$(echo "$output" | jq '.elapsed_minutes')
  # Allow ±2 minutes tolerance for process overhead
  [ "$ELAPSED" -ge 58 ]
  [ "$ELAPSED" -le 62 ]
}

@test "elapsed_minutes is not offset by local timezone" {
  # If the script uses local time instead of UTC to parse a UTC timestamp,
  # the elapsed time will be off by the UTC offset (e.g. ±120 min for UTC+2).
  # We dispatch exactly 30 minutes ago (UTC) and verify result is near 30, not ~150 or ~-90.
  DISPATCH_UTC=$(date -u -v-30M "+%Y-%m-%dT%H:%M:%S" 2>/dev/null \
    || date -u -d "30 minutes ago" "+%Y-%m-%dT%H:%M:%S" 2>/dev/null)

  CONFIG=$(make_config "$DISPATCH_UTC")
  run bash "$WAVE_STATUS" "$CONFIG"
  [ "$status" -eq 0 ]
  ELAPSED=$(echo "$output" | jq '.elapsed_minutes')
  # Should be ~30; if timezone offset was applied incorrectly it would be ~-90 or ~150
  [ "$ELAPSED" -ge 28 ]
  [ "$ELAPSED" -le 32 ]
}

@test "elapsed_minutes is -1 when dispatch_time is missing" {
  cat > "$TEST_TMPDIR/wave-config.json" <<'EOF'
{
  "beads": [
    {"id": "test-aa1", "surface": "surface:1"},
    {"id": "test-bb2", "surface": "surface:2"}
  ]
}
EOF
  run bash "$WAVE_STATUS" "$TEST_TMPDIR/wave-config.json"
  [ "$status" -eq 0 ]
  ELAPSED=$(echo "$output" | jq '.elapsed_minutes')
  [ "$ELAPSED" -eq -1 ]
}

# ---------------------------------------------------------------------------
# Output structure sanity
# ---------------------------------------------------------------------------
@test "output is valid JSON with required top-level keys" {
  CONFIG=$(make_config "2026-04-19T10:00:00")
  run bash "$WAVE_STATUS" "$CONFIG"
  [ "$status" -eq 0 ]
  # Must be valid JSON
  echo "$output" | jq . > /dev/null
  # Must have all required keys
  echo "$output" | jq 'has("elapsed_minutes") and has("beads") and has("all_done") and has("follow_up_beads")' | grep -q true
}

@test "script exits non-zero when config file not found" {
  run bash "$WAVE_STATUS" "/nonexistent/path/wave-config.json"
  [ "$status" -ne 0 ]
}
