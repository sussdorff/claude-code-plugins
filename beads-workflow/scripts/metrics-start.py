#!/usr/bin/env python3
"""
metrics-start.py — Create a bead_runs row and print the run_id.

Usage: metrics-start.py <bead_id> [wave_id] [mode]

  bead_id   — required
  wave_id   — optional; pass "" or omit to leave blank
  mode      — optional; default "quick-fix"

Stdout: run_id (UUID string) on success, empty string on failure.
Stderr: WARNING on failure (never fatal — missing metrics must not abort workflows).

Path resolution: uses SCRIPT_DIR/../lib/orchestrator, so this works from any repo
as long as the script is called via its installed path.
"""

import os
import sys
from pathlib import Path


def main() -> None:
    args = sys.argv[1:]

    if not args:
        print("metrics-start.py: ERROR: bead_id is required", file=sys.stderr)
        sys.exit(1)

    bead_id = args[0]
    wave_id: str | None = args[1] if len(args) > 1 else None
    mode = args[2] if len(args) > 2 else "quick-fix"

    # Normalize wave_id: empty string → None
    if wave_id == "":
        wave_id = None

    script_dir = Path(__file__).resolve().parent
    metrics_dir_override = os.environ.get("METRICS_DIR_OVERRIDE", "")
    if metrics_dir_override:
        metrics_dir = Path(metrics_dir_override)
    else:
        metrics_dir = script_dir.parent / "lib" / "orchestrator"

    db_env = os.environ.get("METRICS_DB_PATH", "")

    sys.path.insert(0, str(metrics_dir))
    try:
        from metrics import DB_PATH, start_run  # type: ignore[import]

        db_path = Path(db_env) if db_env else DB_PATH
        run_id = start_run(bead_id, wave_id=wave_id, mode=mode, db_path=db_path)
        print(run_id)
    except Exception as e:
        print(
            f"metrics-start.py: WARNING: metrics unavailable ({e}) — metrics will not be recorded",
            file=sys.stderr,
        )
        print("")  # empty run_id: codex-exec.py degrades gracefully when RUN_ID is unset


if __name__ == "__main__":
    main()
