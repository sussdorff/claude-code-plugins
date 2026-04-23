#!/usr/bin/env python3
"""
metrics-rollup.py — Roll up a bead run and optionally record Codex review stats.

Usage:
  metrics-rollup.py <run_id>
  metrics-rollup.py <run_id> <bead_id> <total_findings> <regression_count>

  run_id           — required; UUID from metrics-start.py
  bead_id          — required when recording phase2 stats (Codex review results)
  total_findings   — total Codex findings (REGRESSION + advisory)
  regression_count — blocking REGRESSION findings only

When called with only run_id (Phase 16 / bead-orchestrator), only rollup_run runs.
When called with all four args (Phase 4 / quick-fix), update_phase2_metrics also runs.

Stdout: "Metrics updated" or "Metrics skipped: <reason>".
Never exits non-zero — metrics failure must not abort the workflow.

Path resolution: uses SCRIPT_DIR/../lib/orchestrator.
"""

import os
import sys
from pathlib import Path


def main() -> None:
    args = sys.argv[1:]

    run_id = args[0] if args else ""

    if not run_id:
        print(
            "metrics-rollup.py: WARNING: run_id is empty — metrics rollup skipped",
            file=sys.stderr,
        )
        print("Metrics skipped: no run_id")
        sys.exit(0)

    bead_id: str | None = args[1] if len(args) > 1 else None
    total_findings_str = args[2] if len(args) > 2 else ""
    regression_count_str = args[3] if len(args) > 3 else ""

    script_dir = Path(__file__).resolve().parent
    metrics_dir_override = os.environ.get("METRICS_DIR_OVERRIDE", "")
    if metrics_dir_override:
        metrics_dir = Path(metrics_dir_override)
    else:
        metrics_dir = script_dir.parent / "lib" / "orchestrator"

    db_env = os.environ.get("METRICS_DB_PATH", "")

    sys.path.insert(0, str(metrics_dir))
    try:
        from metrics import DB_PATH, rollup_run, update_phase2_metrics  # type: ignore[import]

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


if __name__ == "__main__":
    main()
