#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["pytest>=8.0"]
# ///
"""
Tests for increment_auto_decisions() in beads-workflow/lib/orchestrator/metrics.py
RED phase — this test will fail until increment_auto_decisions is implemented.
"""

import sqlite3
import sys
from pathlib import Path

# Resolve lib/orchestrator on sys.path regardless of working directory
_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "beads-workflow" / "lib" / "orchestrator"))

import pytest
from metrics import increment_auto_decisions, init_db, start_run


def test_increment_auto_decisions_basic(tmp_path: Path) -> None:
    """increment_auto_decisions increments the counter by 1 on each call."""
    db = tmp_path / "test_metrics.db"
    run_id = start_run("TEST-iad-001", db_path=db)

    # Initial value should be 0
    conn = sqlite3.connect(str(db))
    row = conn.execute(
        "SELECT auto_decisions FROM bead_runs WHERE run_id = ?", (run_id,)
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == 0, f"Expected 0, got {row[0]}"

    # After one increment
    increment_auto_decisions(run_id, db_path=db)

    conn = sqlite3.connect(str(db))
    row = conn.execute(
        "SELECT auto_decisions FROM bead_runs WHERE run_id = ?", (run_id,)
    ).fetchone()
    conn.close()
    assert row[0] == 1, f"Expected 1 after first increment, got {row[0]}"


def test_increment_auto_decisions_multiple(tmp_path: Path) -> None:
    """increment_auto_decisions can be called multiple times and accumulates."""
    db = tmp_path / "test_metrics.db"
    run_id = start_run("TEST-iad-002", db_path=db)

    increment_auto_decisions(run_id, db_path=db)
    increment_auto_decisions(run_id, db_path=db)
    increment_auto_decisions(run_id, db_path=db)

    conn = sqlite3.connect(str(db))
    row = conn.execute(
        "SELECT auto_decisions FROM bead_runs WHERE run_id = ?", (run_id,)
    ).fetchone()
    conn.close()
    assert row[0] == 3, f"Expected 3 after three increments, got {row[0]}"


def test_increment_auto_decisions_returns_none(tmp_path: Path) -> None:
    """increment_auto_decisions returns None (void operation)."""
    db = tmp_path / "test_metrics.db"
    run_id = start_run("TEST-iad-003", db_path=db)
    result = increment_auto_decisions(run_id, db_path=db)
    assert result is None, f"Expected None, got {result!r}"


def test_increment_auto_decisions_noop_on_missing_db(tmp_path: Path) -> None:
    """increment_auto_decisions silently does nothing if the DB does not exist."""
    db = tmp_path / "nonexistent.db"
    # Should not raise
    increment_auto_decisions("some-run-id", db_path=db)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
