#!/usr/bin/env bash
# metrics-start.sh — Create a bead_runs row and print the run_id.
#
# Usage: metrics-start.sh <bead_id> [wave_id] [mode]
#
#   bead_id   — required
#   wave_id   — optional; pass "" or omit to leave blank
#   mode      — optional; default "quick-fix"
#
# Stdout: run_id (UUID string) on success, empty string on failure.
# Stderr: WARNING on failure (never fatal — missing metrics must not abort workflows).
#
# Path resolution: mirrors codex-exec.sh — uses SCRIPT_DIR/../lib/orchestrator,
# so this works from any repo as long as the script is called via its installed path.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
METRICS_DIR="${METRICS_DIR_OVERRIDE:-${SCRIPT_DIR}/../lib/orchestrator}"

BEAD_ID="${1:-}"
WAVE_ID="${2:-}"
MODE="${3:-quick-fix}"

if [[ -z "$BEAD_ID" ]]; then
    echo "metrics-start.sh: ERROR: bead_id is required" >&2
    exit 1
fi

python3 - <<PYEOF
import sys
from pathlib import Path

metrics_dir = "${METRICS_DIR}"
bead_id = "${BEAD_ID}"
wave_id = "${WAVE_ID}" or None
mode = "${MODE}"

db_env = __import__("os").environ.get("METRICS_DB_PATH", "")

sys.path.insert(0, metrics_dir)
try:
    from metrics import start_run, DB_PATH
    db_path = Path(db_env) if db_env else DB_PATH
    run_id = start_run(bead_id, wave_id=wave_id, mode=mode, db_path=db_path)
    print(run_id)
except Exception as e:
    print(f"metrics-start.sh: WARNING: metrics unavailable ({e}) — metrics will not be recorded", file=sys.stderr)
    print("")  # empty run_id: codex-exec.sh degrades gracefully when RUN_ID is unset
PYEOF
