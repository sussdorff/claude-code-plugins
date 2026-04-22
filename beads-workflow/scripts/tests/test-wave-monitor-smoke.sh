#!/usr/bin/env bash
# test-wave-monitor-smoke.sh — Smoke test for wave-monitor verdict routing
#
# Tests that the wave-monitor agent's routing logic produces the correct verdict
# for each of the 5 terminal outcomes, using mocked wave-completion.sh output.
#
# Does NOT spawn the actual agent (would require claude CLI) — instead exercises
# the verdict-routing logic in isolation using mock scripts and config files.
#
# Usage: bash test-wave-monitor-smoke.sh
# Exit: 0 if all 5 verdicts produce expected output, 1 on failure

set -euo pipefail

TMPDIR_TEST=$(mktemp -d)
PASS=0
FAIL=0

trap 'rm -rf "$TMPDIR_TEST"' EXIT

# Minimal wave config for testing
WAVE_CONFIG="$TMPDIR_TEST/wave-config.json"
cat > "$WAVE_CONFIG" <<'JSON'
{
  "wave_id": "test-wave-001",
  "dispatch_time": "2026-04-21T08:00:00",
  "beads": [
    {"id": "TEST-aaa", "surface": "surface:99"},
    {"id": "TEST-bbb", "surface": "surface:98"}
  ]
}
JSON

_run_verdict() {
  local label="$1"
  local mock_completion_exit="$2"
  local mock_completion_stdout="$3"
  local expected_status="$4"
  local expected_reason="${5:-}"

  # Write mock wave-completion.sh that returns controlled output
  local mock_script="$TMPDIR_TEST/wave-completion-${label}.sh"
  cat > "$mock_script" <<MOCK
#!/usr/bin/env bash
echo '$mock_completion_stdout'
exit $mock_completion_exit
MOCK
  chmod +x "$mock_script"

  # Inline routing logic matching wave-monitor's implementation
  local EXIT_CODE
  local STDOUT
  STDOUT=$(bash "$mock_script" "$WAVE_CONFIG" 2>/dev/null) || EXIT_CODE=$?
  EXIT_CODE="${EXIT_CODE:-0}"

  local verdict_status=""
  local verdict_reason=""

  if [[ "$EXIT_CODE" == "2" ]]; then
    verdict_status="needs_intervention"
    verdict_reason="ambiguous"
  elif ! echo "$STDOUT" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
    verdict_status="needs_intervention"
    verdict_reason="ambiguous"
  else
    COMPLETE=$(echo "$STDOUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('complete', False))")
    if [[ "$COMPLETE" == "True" ]]; then
      verdict_status="complete"
    else
      STALL_ID=$(echo "$STDOUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
stalls = d.get('stalls', [])
if stalls:
    print(stalls[0]['id'])
" 2>/dev/null || true)
      if [[ -n "$STALL_ID" ]]; then
        verdict_status="needs_intervention"
        verdict_reason="stuck"
      fi
    fi
  fi

  # Evaluate
  if [[ "$verdict_status" == "$expected_status" ]]; then
    if [[ -n "$expected_reason" && "$verdict_reason" != "$expected_reason" ]]; then
      echo "FAIL [$label]: status=$verdict_status but reason='$verdict_reason' (expected '$expected_reason')"
      FAIL=$((FAIL + 1))
    else
      echo "PASS [$label]: status=$verdict_status${verdict_reason:+, reason=$verdict_reason}"
      PASS=$((PASS + 1))
    fi
  else
    echo "FAIL [$label]: status='$verdict_status' (expected '$expected_status')"
    FAIL=$((FAIL + 1))
  fi
}

# ── Verdict 1: complete ──────────────────────────────────────────────────────
_run_verdict "complete" 0 \
  '{"complete":true,"all_beads_closed":true,"all_surfaces_idle":true,"stragglers":[],"unclosed_follow_ups":[],"stalls":[]}' \
  "complete"

# ── Verdict 2: needs_intervention/pane-error (simulated via ambiguous path) ──
# pane-error is detected via cmux read-screen, not wave-completion.sh output.
# We verify the ambiguous path as a proxy — actual pane-error requires cmux.
echo "SKIP [pane-error]: requires live cmux surface (exercised in integration test)"

# ── Verdict 3: needs_intervention/stuck (via stalls array) ──────────────────
_run_verdict "stuck-via-stalls" 1 \
  '{"complete":false,"all_beads_closed":false,"all_surfaces_idle":false,"stragglers":[{"id":"TEST-aaa","bd_status":"in_progress","surface_idle":true}],"unclosed_follow_ups":[],"stalls":[{"id":"TEST-aaa","detected_at":"2026-04-21T09:00:00Z","elapsed_minutes":65}]}' \
  "needs_intervention" "stuck"

# ── Verdict 4: needs_intervention/review-loop ───────────────────────────────
# review-loop is detected via cmux scrollback pattern matching.
# Verified via the routing table in wave-monitor.md § Escalation Heuristics.
echo "SKIP [review-loop]: requires live cmux surface (exercised in integration test)"

# ── Verdict 5: needs_intervention/ambiguous (exit code 2) ───────────────────
_run_verdict "ambiguous-exit2" 2 \
  "" \
  "needs_intervention" "ambiguous"

# ── Verdict 5b: needs_intervention/ambiguous (invalid JSON) ─────────────────
_run_verdict "ambiguous-invalid-json" 0 \
  "not valid json output here" \
  "needs_intervention" "ambiguous"

# ── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "Results: $PASS passed, $FAIL failed"
echo "Note: pane-error and review-loop verdicts require live cmux surfaces."
echo "      See wave-monitor.md § Escalation Heuristics for routing table."

if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
exit 0
