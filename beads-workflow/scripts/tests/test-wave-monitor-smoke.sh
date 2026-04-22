#!/usr/bin/env bash
# test-wave-monitor-smoke.sh — Smoke test for wave-monitor verdict routing via wave-poll.py
#
# Tests that wave-poll.py produces the correct verdict for each terminal outcome
# using mocked wave-completion.sh output injected via WAVE_COMPLETION_OVERRIDE.
#
# Replaces inline routing logic with direct delegation to wave-poll.py,
# so the smoke test exercises the actual helper rather than duplicating it.
#
# Usage: bash test-wave-monitor-smoke.sh
# Exit: 0 if all verdicts produce expected output, 1 on failure

set -euo pipefail

TMPDIR_TEST=$(mktemp -d)
PASS=0
FAIL=0

trap 'rm -rf "$TMPDIR_TEST"' EXIT

# Locate wave-poll.py
WAVE_POLL=$(find ~/.claude -name "wave-poll.py" 2>/dev/null | head -1)
WAVE_POLL="${WAVE_POLL:-$(find . -name "wave-poll.py" 2>/dev/null | head -1)}"

if [[ -z "$WAVE_POLL" ]]; then
  echo "FATAL: wave-poll.py not found in ~/.claude or local tree"
  exit 1
fi

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

  # Invoke wave-poll.py with the mock script injected via env override
  local verdict
  verdict=$(
    WAVE_COMPLETION_OVERRIDE="$mock_script" \
    python3 "$WAVE_POLL" \
      --config "$WAVE_CONFIG" \
      --poll-interval 0 \
      --stuck-hours 4 \
      --review-max 3 \
    2>/dev/null
  ) || true

  # wave-poll.py now returns execution-result envelope; extract data.verdict
  local verdict_status
  local verdict_reason
  verdict_status=$(echo "$verdict" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['verdict'].get('status',''))" 2>/dev/null || echo "")
  verdict_reason=$(echo "$verdict" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['verdict'].get('reason',''))" 2>/dev/null || echo "")

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

# ── Verdict 2: needs_intervention/pane-error ────────────────────────────────
# pane-error is detected via cmux read-screen, not wave-completion.sh output.
echo "SKIP [pane-error]: requires live cmux surface (exercised in integration test)"

# ── Verdict 3: needs_intervention/stuck (via stalls array) ──────────────────
_run_verdict "stuck-via-stalls" 1 \
  '{"complete":false,"all_beads_closed":false,"all_surfaces_idle":false,"stragglers":[{"id":"TEST-aaa","bd_status":"in_progress","surface_idle":true}],"unclosed_follow_ups":[],"stalls":[{"id":"TEST-aaa","detected_at":"2026-04-21T09:00:00Z","elapsed_minutes":65}]}' \
  "needs_intervention" "stuck"

# ── Verdict 4: needs_intervention/review-loop ───────────────────────────────
# review-loop is detected via cmux scrollback pattern matching.
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
