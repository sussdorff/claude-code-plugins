#!/usr/bin/env bash
# metrics-rollup.sh — Roll up a bead run and optionally record Codex review stats.
#
# Usage:
#   metrics-rollup.sh <run_id>
#   metrics-rollup.sh <run_id> <bead_id> <total_findings> <regression_count>
#
#   run_id           — required; UUID from metrics-start.sh
#   bead_id          — required when recording phase2 stats (Codex review results)
#   total_findings   — total Codex findings (REGRESSION + advisory)
#   regression_count — blocking REGRESSION findings only
#
# When called with only run_id (Phase 16 / bead-orchestrator), only rollup_run runs.
# When called with all four args (Phase 4 / quick-fix), update_phase2_metrics also runs.
#
# Stdout: "Metrics updated" or "Metrics skipped: <reason>".
# Never exits non-zero — metrics failure must not abort the workflow.
#
# Path resolution: mirrors codex-exec.sh — uses SCRIPT_DIR/../lib/orchestrator.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
METRICS_DIR="${METRICS_DIR_OVERRIDE:-${SCRIPT_DIR}/../lib/orchestrator}"

RUN_ID="${1:-}"
BEAD_ID="${2:-}"
TOTAL_FINDINGS="${3:-}"
REGRESSION_COUNT="${4:-}"

if [[ -z "$RUN_ID" ]]; then
    echo "metrics-rollup.sh: WARNING: run_id is empty — metrics rollup skipped" >&2
    echo "Metrics skipped: no run_id"
    exit 0
fi

python3 - <<PYEOF
import sys
from pathlib import Path

metrics_dir = "${METRICS_DIR}"
run_id = "${RUN_ID}"
bead_id = "${BEAD_ID}" or None
total_findings_str = "${TOTAL_FINDINGS}"
regression_count_str = "${REGRESSION_COUNT}"

db_env = __import__("os").environ.get("METRICS_DB_PATH", "")

sys.path.insert(0, metrics_dir)
try:
    from metrics import rollup_run, update_phase2_metrics, DB_PATH
    db_path = Path(db_env) if db_env else DB_PATH

    rollup_run(run_id, db_path=db_path)

    # Record Codex review stats when caller provides all four args
    if bead_id and total_findings_str and regression_count_str:
        update_phase2_metrics(
            bead_id=bead_id,
            triggered=True,
            findings=int(total_findings_str),
            critical=int(regression_count_str),
            run_id=run_id,
            db_path=db_path,
        )

    print("Metrics updated")
except Exception as e:
    print(f"Metrics skipped: {e}")
PYEOF
