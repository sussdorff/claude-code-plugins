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

# ---------------------------------------------------------------------------
# Temp file for capturing codex output (cleaned up on exit)
# ---------------------------------------------------------------------------
TMPFILE="$(mktemp)"
trap 'rm -f "$TMPFILE"' EXIT

# ---------------------------------------------------------------------------
# Run codex, tee output to temp file (stdout unchanged)
# ---------------------------------------------------------------------------
START_MS=$(python3 -c "import time; print(int(time.time() * 1000))")

CODEX_EXIT=0
codex exec --json "$@" | tee "$TMPFILE"
# Capture codex's exit code from PIPESTATUS (index 0 = codex, index 1 = tee).
# pipefail is set, so the pipeline exit reflects the first failing command,
# but PIPESTATUS gives per-command codes regardless.
CODEX_EXIT="${PIPESTATUS[0]}"

END_MS=$(python3 -c "import time; print(int(time.time() * 1000))")
DURATION_MS=$(( END_MS - START_MS ))

# ---------------------------------------------------------------------------
# Parse ALL turn.completed events from temp file, sum usage fields
# ---------------------------------------------------------------------------
python3 - <<PYEOF
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

# Sum usage across all turn.completed events
total_input = 0
total_cached = 0
total_output = 0

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
            total_input  += usage.get("input_tokens", 0)
            total_cached += usage.get("cached_input_tokens", 0)
            total_output += usage.get("output_tokens", 0)

total_tokens = total_input + total_output

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
    reasoning_output_tokens=0,
    total_tokens=total_tokens,
    duration_ms=duration_ms,
    exit_code=exit_code,
    wave_id=wave_id if wave_id else None,
    db_path=db_path,
)
PYEOF

# ---------------------------------------------------------------------------
# Propagate codex's exact exit code
# ---------------------------------------------------------------------------
exit "$CODEX_EXIT"
