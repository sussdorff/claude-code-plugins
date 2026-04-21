#!/usr/bin/env bash
# codex-exec.sh — Thin wrapper around 'codex exec --json' that records usage
# from turn.completed events into metrics.db via metrics.insert_agent_call().
#
# Required env vars:
#   RUN_ID       — bead_runs.run_id this Codex call belongs to
#   BEAD_ID      — for denormalized query convenience
#   PHASE_LABEL  — one of: codex-adversarial | codex-review | codex-fix-check
#
# Optional env vars:
#   WAVE_ID      — if set, forwarded to insert_agent_call
#   ITERATION    — integer, default 1
#
# Exit code: propagates codex's exact exit code.
# Errors (missing env vars, missing module): stderr + exit 1 (no DB write).

set -uo pipefail

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Allow test override; default to the canonical relative path
METRICS_DIR="${METRICS_DIR_OVERRIDE:-${SCRIPT_DIR}/../lib/orchestrator}"

# ---------------------------------------------------------------------------
# Validate required env vars
# ---------------------------------------------------------------------------
if [[ -z "${RUN_ID:-}" ]]; then
    echo "codex-exec.sh: ERROR: RUN_ID is not set" >&2
    exit 1
fi
if [[ -z "${BEAD_ID:-}" ]]; then
    echo "codex-exec.sh: ERROR: BEAD_ID is not set" >&2
    exit 1
fi
if [[ -z "${PHASE_LABEL:-}" ]]; then
    echo "codex-exec.sh: ERROR: PHASE_LABEL is not set" >&2
    exit 1
fi

ITERATION="${ITERATION:-1}"
WAVE_ID="${WAVE_ID:-}"

# ---------------------------------------------------------------------------
# Validate Python / metrics module availability
# ---------------------------------------------------------------------------
if ! python3 -c "import sys; sys.path.insert(0, '${METRICS_DIR}'); from metrics import insert_agent_call" 2>/dev/null; then
    echo "codex-exec.sh: ERROR: Cannot import insert_agent_call from ${METRICS_DIR}/metrics.py" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Read model from ~/.codex/config.toml (or CODEX_CONFIG_PATH override)
# ---------------------------------------------------------------------------
CODEX_CONFIG="${CODEX_CONFIG_PATH:-${HOME}/.codex/config.toml}"
MODEL="codex"
if [[ -f "$CODEX_CONFIG" ]]; then
    _model_line=$(grep '^model = ' "$CODEX_CONFIG" | head -1 || true)
    if [[ -n "$_model_line" ]]; then
        # Extract value between quotes: model = "gpt-5.4" → gpt-5.4
        MODEL=$(echo "$_model_line" | sed 's/^model = "\(.*\)"/\1/')
    fi
fi
# Normalize model name so rollup_run's SQL filter (model LIKE '%codex%' OR model LIKE
# '%o1%' OR model LIKE '%o3%') matches.  If the extracted model matches none of those
# patterns (e.g. "gpt-5.4"), prefix it with "codex/" so it matches '%codex%'.
if [[ "$MODEL" != *codex* && "$MODEL" != *o1* && "$MODEL" != *o3* ]]; then
    MODEL="codex/${MODEL}"
fi

# ---------------------------------------------------------------------------
# Temp file for capturing codex output (cleaned up on exit)
# ---------------------------------------------------------------------------
TMPFILE="$(mktemp)"
trap 'rm -f "$TMPFILE"' EXIT

# ---------------------------------------------------------------------------
# Detect timeout utility (CCP-dzp): prefer GNU `timeout`, fall back to
# `gtimeout` (Homebrew coreutils on macOS). If neither is available, run
# codex unwrapped — degraded-but-working beats hard-failing on minimal systems.
# A stalled codex without a timeout is a regression, but losing the wrapper
# entirely would be worse.
# ---------------------------------------------------------------------------
CODEX_EXEC_TIMEOUT="${CODEX_EXEC_TIMEOUT:-300}"
TIMEOUT_CMD=()
if command -v timeout >/dev/null 2>&1; then
    TIMEOUT_CMD=(timeout "$CODEX_EXEC_TIMEOUT")
elif command -v gtimeout >/dev/null 2>&1; then
    TIMEOUT_CMD=(gtimeout "$CODEX_EXEC_TIMEOUT")
else
    echo "codex-exec.sh: WARNING: neither 'timeout' nor 'gtimeout' found; running codex without a timeout" >&2
fi

# ---------------------------------------------------------------------------
# Run codex, tee output to temp file (stdout unchanged)
# ---------------------------------------------------------------------------
START_MS=$(python3 -c "import time; print(int(time.time() * 1000))")

CODEX_EXIT=0
"${TIMEOUT_CMD[@]}" codex exec --json "$@" | tee "$TMPFILE"
# Capture codex's (or timeout's) exit code from PIPESTATUS (index 0 = left side
# of pipe, index 1 = tee). When TIMEOUT_CMD is set and the timeout fires, the
# `timeout` utility exits 124; that 124 flows through PIPESTATUS[0] into
# CODEX_EXIT and out via the final `exit "$CODEX_EXIT"` — the acceptance
# criterion for CCP-dzp.
CODEX_EXIT="${PIPESTATUS[0]}"

END_MS=$(python3 -c "import time; print(int(time.time() * 1000))")
DURATION_MS=$(( END_MS - START_MS ))

# ---------------------------------------------------------------------------
# Parse ALL turn.completed events from temp file, sum usage fields
# ---------------------------------------------------------------------------
PYTHON_EXIT=0
python3 - <<PYEOF || PYTHON_EXIT=$?
import sys
import json
import os
from pathlib import Path

tmpfile = "${TMPFILE}"
metrics_dir = "${METRICS_DIR}"
run_id = "${RUN_ID}"
bead_id = "${BEAD_ID}"
phase_label = "${PHASE_LABEL}"
wave_id = "${WAVE_ID}" or None
iteration = int("${ITERATION}")
model = "${MODEL}"
duration_ms = int("${DURATION_MS}")
exit_code = int("${CODEX_EXIT}")

# Optional DB path override for testing
_db_env = os.environ.get("METRICS_DB_PATH", "")

# Sum usage across all turn.completed events.
# Project convention (matches parse_usage() and test_metrics_run_api.py):
#   total = input + cached_input + output + reasoning  (all fields additive)
total_input = 0
total_cached = 0
total_output = 0
total_reasoning = 0

with open(tmpfile) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "turn.completed":
            usage = event.get("usage", {})
            total_input    += usage.get("input_tokens", 0)
            total_cached   += usage.get("cached_input_tokens", 0)
            total_output   += usage.get("output_tokens", 0)
            total_reasoning += usage.get("reasoning_output_tokens", 0)

total_tokens = total_input + total_cached + total_output + total_reasoning

if total_tokens == 0:
    print("codex-exec.sh: WARNING: no turn.completed events found — no DB record written", file=sys.stderr)
    sys.exit(0)

sys.path.insert(0, metrics_dir)
from metrics import insert_agent_call, DB_PATH

db_path = Path(_db_env) if _db_env else DB_PATH

insert_agent_call(
    run_id=run_id,
    bead_id=bead_id,
    phase_label=phase_label,
    agent_label="codex",
    model=model,
    iteration=iteration,
    input_tokens=total_input,
    cached_input_tokens=total_cached,
    output_tokens=total_output,
    reasoning_output_tokens=total_reasoning,
    total_tokens=total_tokens,
    duration_ms=duration_ms,
    exit_code=exit_code,
    wave_id=wave_id if wave_id else None,
    db_path=db_path,
)
PYEOF

if [[ $PYTHON_EXIT -ne 0 ]]; then
    echo "codex-exec.sh: ERROR: metrics recording failed (python exit $PYTHON_EXIT)" >&2
    exit $PYTHON_EXIT
fi

# ---------------------------------------------------------------------------
# Propagate codex's exact exit code
# ---------------------------------------------------------------------------
exit "$CODEX_EXIT"
