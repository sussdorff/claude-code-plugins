#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["pytest>=8.0"]
# ///
"""
Tests for metrics-start.sh and metrics-rollup.sh.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "beads-workflow" / "lib" / "orchestrator"))

from metrics import get_run, init_db, rollup_run, start_run

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
_METRICS_START = _SCRIPTS_DIR / "metrics-start.sh"
_METRICS_ROLLUP = _SCRIPTS_DIR / "metrics-rollup.sh"
_METRICS_DIR = str(_REPO_ROOT / "beads-workflow" / "lib" / "orchestrator")


def _env(db: Path) -> dict:
    env = os.environ.copy()
    env["METRICS_DB_PATH"] = str(db)
    env["METRICS_DIR_OVERRIDE"] = _METRICS_DIR
    return env


# ---------------------------------------------------------------------------
# metrics-start.sh
# ---------------------------------------------------------------------------

def test_metrics_start_creates_run(tmp_path: Path) -> None:
    """metrics-start.sh must print a non-empty run_id and create a bead_runs row."""
    db = tmp_path / "metrics.db"
    env = _env(db)

    result = subprocess.run(
        ["bash", str(_METRICS_START), "TEST-bead-1", "", "quick-fix"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    run_id = result.stdout.strip()
    assert run_id, "Expected non-empty run_id on stdout"

    row = get_run(run_id, db_path=db)
    assert row["bead_id"] == "TEST-bead-1"
    assert row["mode"] == "quick-fix"
    assert row["wave_id"] == ""


def test_metrics_start_with_wave_id(tmp_path: Path) -> None:
    """metrics-start.sh passes wave_id through to the DB row."""
    db = tmp_path / "metrics.db"
    env = _env(db)

    result = subprocess.run(
        ["bash", str(_METRICS_START), "TEST-bead-2", "wave-xyz", "full-1pane"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    run_id = result.stdout.strip()
    row = get_run(run_id, db_path=db)
    assert row["wave_id"] == "wave-xyz"
    assert row["mode"] == "full-1pane"


def test_metrics_start_missing_bead_id_exits_nonzero(tmp_path: Path) -> None:
    """metrics-start.sh with no args must exit non-zero."""
    result = subprocess.run(
        ["bash", str(_METRICS_START)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "ERROR" in result.stderr


def test_metrics_start_bad_metrics_dir_prints_warning_and_empty(tmp_path: Path) -> None:
    """When metrics module is unreachable, prints empty string + WARNING (never fatal)."""
    env = os.environ.copy()
    env["METRICS_DIR_OVERRIDE"] = "/nonexistent/path"
    env.pop("METRICS_DB_PATH", None)

    result = subprocess.run(
        ["bash", str(_METRICS_START), "TEST-bead-3", "", "quick-fix"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Should exit 0 even when metrics unavailable; stderr={result.stderr!r}"
    assert result.stdout.strip() == "", f"Expected empty stdout, got: {result.stdout!r}"
    assert "WARNING" in result.stderr


# ---------------------------------------------------------------------------
# metrics-rollup.sh
# ---------------------------------------------------------------------------

def test_metrics_rollup_only_run_id(tmp_path: Path) -> None:
    """metrics-rollup.sh with just run_id must call rollup_run and print 'Metrics updated'."""
    db = tmp_path / "metrics.db"
    run_id = start_run("TEST-bead-rollup", mode="quick-fix", db_path=db)
    env = _env(db)

    result = subprocess.run(
        ["bash", str(_METRICS_ROLLUP), run_id],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    assert "Metrics updated" in result.stdout


def test_metrics_rollup_with_phase2_stats(tmp_path: Path) -> None:
    """metrics-rollup.sh with all 4 args must update phase2 columns."""
    import sqlite3

    db = tmp_path / "metrics.db"
    run_id = start_run("TEST-bead-p2", mode="quick-fix", db_path=db)
    env = _env(db)

    result = subprocess.run(
        ["bash", str(_METRICS_ROLLUP), run_id, "TEST-bead-p2", "5", "2"],
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


def test_metrics_rollup_empty_run_id_is_noop(tmp_path: Path) -> None:
    """metrics-rollup.sh with empty run_id must exit 0 silently (noop)."""
    result = subprocess.run(
        ["bash", str(_METRICS_ROLLUP), ""],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "skipped" in result.stdout.lower()


def test_metrics_rollup_bad_metrics_dir_still_exits_zero(tmp_path: Path) -> None:
    """When metrics module is unreachable, rollup exits 0 and prints 'Metrics skipped'."""
    env = os.environ.copy()
    env["METRICS_DIR_OVERRIDE"] = "/nonexistent/path"

    result = subprocess.run(
        ["bash", str(_METRICS_ROLLUP), "some-run-id"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Should never be fatal; stderr={result.stderr!r}"
    assert "skipped" in result.stdout.lower() or "Metrics skipped" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
