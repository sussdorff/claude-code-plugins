#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["pytest>=8.0"]
# ///
"""
Tests for metrics-start.py and metrics-rollup.py (Python equivalents of the .sh scripts).

These tests mirror test_metrics_scripts.py but target the Python scripts directly,
invoked via python3 rather than bash.
"""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "beads-workflow" / "lib" / "orchestrator"))

from metrics import get_run, init_db, rollup_run, start_run

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
_METRICS_START_PY = _SCRIPTS_DIR / "metrics-start.py"
_METRICS_ROLLUP_PY = _SCRIPTS_DIR / "metrics-rollup.py"
_METRICS_DIR = str(_REPO_ROOT / "beads-workflow" / "lib" / "orchestrator")


def _env(db: Path) -> dict:
    env = os.environ.copy()
    env["METRICS_DB_PATH"] = str(db)
    env["METRICS_DIR_OVERRIDE"] = _METRICS_DIR
    return env


# ---------------------------------------------------------------------------
# metrics-start.py
# ---------------------------------------------------------------------------


def test_metrics_start_py_creates_run(tmp_path: Path) -> None:
    """metrics-start.py must print a non-empty run_id and create a bead_runs row."""
    db = tmp_path / "metrics.db"
    env = _env(db)

    result = subprocess.run(
        ["python3", str(_METRICS_START_PY), "TEST-bead-py-1", "", "quick-fix"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    run_id = result.stdout.strip()
    assert run_id, "Expected non-empty run_id on stdout"

    row = get_run(run_id, db_path=db)
    assert row["bead_id"] == "TEST-bead-py-1"
    assert row["mode"] == "quick-fix"
    assert row["wave_id"] == ""


def test_metrics_start_py_with_wave_id(tmp_path: Path) -> None:
    """metrics-start.py passes wave_id through to the DB row."""
    db = tmp_path / "metrics.db"
    env = _env(db)

    result = subprocess.run(
        ["python3", str(_METRICS_START_PY), "TEST-bead-py-2", "wave-xyz", "full-1pane"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    run_id = result.stdout.strip()
    row = get_run(run_id, db_path=db)
    assert row["wave_id"] == "wave-xyz"
    assert row["mode"] == "full-1pane"


def test_metrics_start_py_missing_bead_id_exits_nonzero(tmp_path: Path) -> None:
    """metrics-start.py with no args must exit non-zero."""
    result = subprocess.run(
        ["python3", str(_METRICS_START_PY)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "ERROR" in result.stderr


def test_metrics_start_py_bad_metrics_dir_prints_warning_and_empty(tmp_path: Path) -> None:
    """When metrics module is unreachable, prints empty string + WARNING (never fatal)."""
    env = os.environ.copy()
    env["METRICS_DIR_OVERRIDE"] = "/nonexistent/path"
    env.pop("METRICS_DB_PATH", None)

    result = subprocess.run(
        ["python3", str(_METRICS_START_PY), "TEST-bead-py-3", "", "quick-fix"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Should exit 0 even when metrics unavailable; stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "", f"Expected empty stdout, got: {result.stdout!r}"
    assert "WARNING" in result.stderr


# ---------------------------------------------------------------------------
# metrics-rollup.py
# ---------------------------------------------------------------------------


def test_metrics_rollup_py_only_run_id(tmp_path: Path) -> None:
    """metrics-rollup.py with just run_id must call rollup_run and print 'Metrics updated'."""
    db = tmp_path / "metrics.db"
    run_id = start_run("TEST-bead-py-rollup", mode="quick-fix", db_path=db)
    env = _env(db)

    result = subprocess.run(
        ["python3", str(_METRICS_ROLLUP_PY), run_id],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    assert "Metrics updated" in result.stdout


def test_metrics_rollup_py_with_phase2_stats(tmp_path: Path) -> None:
    """metrics-rollup.py with all 4 args must update phase2 columns."""
    db = tmp_path / "metrics.db"
    run_id = start_run("TEST-bead-py-p2", mode="quick-fix", db_path=db)
    env = _env(db)

    result = subprocess.run(
        ["python3", str(_METRICS_ROLLUP_PY), run_id, "TEST-bead-py-p2", "5", "2"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    assert "Metrics updated" in result.stdout

    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT phase2_triggered, phase2_findings, phase2_critical FROM bead_runs WHERE run_id = ?",
        (run_id,),
    ).fetchone()
    conn.close()

    assert row["phase2_triggered"] == 1
    assert row["phase2_findings"] == 5
    assert row["phase2_critical"] == 2


def test_metrics_rollup_py_empty_run_id_is_noop(tmp_path: Path) -> None:
    """metrics-rollup.py with empty run_id must exit 0 silently (noop)."""
    result = subprocess.run(
        ["python3", str(_METRICS_ROLLUP_PY), ""],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "skipped" in result.stdout.lower()


def test_metrics_rollup_py_bad_metrics_dir_still_exits_zero(tmp_path: Path) -> None:
    """When metrics module is unreachable, rollup exits 0 and prints 'Metrics skipped'."""
    env = os.environ.copy()
    env["METRICS_DIR_OVERRIDE"] = "/nonexistent/path"

    result = subprocess.run(
        ["python3", str(_METRICS_ROLLUP_PY), "some-run-id"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Should never be fatal; stderr={result.stderr!r}"
    assert "skipped" in result.stdout.lower() or "Metrics skipped" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
