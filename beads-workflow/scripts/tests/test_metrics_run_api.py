#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["pytest>=8.0"]
# ///
"""
Roundtrip tests for the CCP-2vo.2 metrics run API:
start_run, insert_agent_call, rollup_run, get_run
"""

import logging
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# Resolve lib/orchestrator on sys.path regardless of working directory
_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "beads-workflow" / "lib" / "orchestrator"))

import pytest
from metrics import get_run, init_db, insert_agent_call, rollup_run, start_run, update_phase2_metrics


def test_roundtrip(tmp_path: Path) -> None:
    db = tmp_path / "test_metrics.db"

    # 1. start_run
    run_id = start_run("TEST-123", wave_id="wave-1", mode="quick-fix", db_path=db)
    assert run_id, "run_id must be non-empty"
    assert len(run_id) == 36, f"UUID4 should be 36 chars, got {len(run_id)}"

    # 2. insert_agent_call — Claude Sonnet call (impl phase)
    row_id = insert_agent_call(
        run_id=run_id,
        bead_id="TEST-123",
        phase_label="impl",
        agent_label="implementer",
        model="claude-sonnet-4-5",
        iteration=1,
        input_tokens=1000,
        cached_input_tokens=200,
        output_tokens=500,
        reasoning_output_tokens=0,
        total_tokens=1700,
        duration_ms=5000,
        exit_code=0,
        wave_id="wave-1",
        db_path=db,
    )
    assert row_id > 0

    # insert a second call (o3-mini = codex model)
    insert_agent_call(
        run_id=run_id,
        bead_id="TEST-123",
        phase_label="codex-review",
        agent_label="codex",
        model="o3-mini",
        iteration=1,
        input_tokens=2000,
        cached_input_tokens=0,
        output_tokens=300,
        reasoning_output_tokens=100,
        total_tokens=2400,
        duration_ms=8000,
        exit_code=0,
        wave_id="wave-1",
        db_path=db,
    )

    # 3. rollup_run
    rollup_run(run_id, db_path=db)

    # 4. get_run and verify rollup
    run = get_run(run_id, db_path=db)
    assert run["bead_id"] == "TEST-123"
    assert run["run_id"] == run_id
    assert run["codex_total_tokens"] == 2400, (
        f"Expected codex_total_tokens=2400, got {run['codex_total_tokens']}"
    )
    assert run["codex_runs"] == 1, f"Expected codex_runs=1, got {run['codex_runs']}"

    # 5. Error case: invalid run_id raises ValueError
    with pytest.raises(ValueError):
        insert_agent_call(
            run_id="nonexistent-run-id",
            bead_id="X",
            phase_label="p",
            agent_label="a",
            model="m",
            iteration=1,
            input_tokens=0,
            cached_input_tokens=0,
            output_tokens=0,
            reasoning_output_tokens=0,
            total_tokens=0,
            duration_ms=0,
            exit_code=0,
            db_path=db,
        )

    # 6. get_run raises KeyError for missing run
    with pytest.raises(KeyError):
        get_run("no-such-run", db_path=db)

    # 7. Multiple runs of same bead_id are valid
    run_id2 = start_run("TEST-123", mode="quick-fix", db_path=db)
    assert run_id2 != run_id, "Each start_run must produce a unique run_id"


def test_two_runs_same_bead_isolated(tmp_path: Path) -> None:
    """Two runs of the same bead on the same date must stay isolated."""
    db = tmp_path / "iso.db"
    run_a = start_run("SAME-BEAD", mode="quick-fix", db_path=db)
    run_b = start_run("SAME-BEAD", mode="quick-fix", db_path=db)

    insert_agent_call(
        run_id=run_a,
        bead_id="SAME-BEAD",
        phase_label="impl",
        agent_label="impl-a",
        model="claude-sonnet-4-5",
        iteration=1,
        input_tokens=1000,
        cached_input_tokens=0,
        output_tokens=500,
        reasoning_output_tokens=0,
        total_tokens=1500,
        duration_ms=3000,
        exit_code=0,
        db_path=db,
    )

    insert_agent_call(
        run_id=run_b,
        bead_id="SAME-BEAD",
        phase_label="impl",
        agent_label="impl-b",
        model="claude-sonnet-4-5",
        iteration=1,
        input_tokens=2000,
        cached_input_tokens=0,
        output_tokens=800,
        reasoning_output_tokens=0,
        total_tokens=2800,
        duration_ms=5000,
        exit_code=0,
        db_path=db,
    )

    rollup_run(run_a, db_path=db)
    rollup_run(run_b, db_path=db)

    run_a_data = get_run(run_a, db_path=db)
    run_b_data = get_run(run_b, db_path=db)

    # Runs must be isolated — no cross-contamination
    assert run_a_data["run_id"] == run_a
    assert run_b_data["run_id"] == run_b

    # phase2 isolation
    update_phase2_metrics("SAME-BEAD", triggered=True, findings=3, critical=1, run_id=run_a, db_path=db)
    run_a_updated = get_run(run_a, db_path=db)
    run_b_unchanged = get_run(run_b, db_path=db)
    assert run_a_updated["phase2_critical"] == 1
    assert run_b_unchanged["phase2_critical"] == 0  # must NOT be contaminated


def test_init_db_idempotent(tmp_path: Path) -> None:
    db = tmp_path / "idem_metrics.db"
    # Calling init_db twice must not raise
    conn1 = init_db(db)
    conn1.close()
    conn2 = init_db(db)
    conn2.close()


def test_rollup_null_run_id(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """
    CCP-imb regression: rollup_run() must not silently drop work when given
    a null/empty run_id, and must surface orphan agent_calls rows (run_id IS NULL)
    via a clear log warning instead of silently ignoring them.

    Before the fix: rollup_run(None) returned silently because SQLite binds None
    as NULL and `WHERE run_id = NULL` matches no rows — unattributed usage was
    silently dropped rather than flagged.
    """
    db = tmp_path / "null_rollup.db"

    # Sanity: a normal rollup still works end-to-end (existing happy path).
    valid_run = start_run("NULL-BEAD", mode="quick-fix", db_path=db)
    insert_agent_call(
        run_id=valid_run,
        bead_id="NULL-BEAD",
        phase_label="impl",
        agent_label="impl",
        model="claude-sonnet-4-5",
        iteration=1,
        input_tokens=100,
        cached_input_tokens=0,
        output_tokens=50,
        reasoning_output_tokens=0,
        total_tokens=150,
        duration_ms=1000,
        exit_code=0,
        db_path=db,
    )
    # Happy-path rollup must still succeed.
    rollup_run(valid_run, db_path=db)

    # (a) rollup_run(None) must NOT raise AttributeError and must NOT silently
    # return — it must raise ValueError so the caller sees the unattributed
    # work instead of losing it.
    with pytest.raises(ValueError):
        rollup_run(None, db_path=db)  # type: ignore[arg-type]

    # Empty-string run_id is equivalent to null for rollup purposes.
    with pytest.raises(ValueError):
        rollup_run("", db_path=db)

    # (b) Orphan agent_calls rows (run_id IS NULL) can exist on databases that
    # were created before run_id was enforced NOT NULL (legacy / cross-schema).
    # Seed one by bypassing insert_agent_call's FK check and writing raw SQL.
    conn = sqlite3.connect(db)
    try:
        # Temporarily allow NULL on run_id by rebuilding agent_calls without the
        # NOT NULL constraint. This mirrors a DB upgraded from a pre-CCP-2vo.2
        # schema where run_id was nullable.
        conn.execute("ALTER TABLE agent_calls RENAME TO agent_calls_strict")
        conn.execute(
            """
            CREATE TABLE agent_calls (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id TEXT,
              bead_id TEXT NOT NULL,
              wave_id TEXT,
              phase_label TEXT NOT NULL,
              agent_label TEXT NOT NULL,
              model TEXT NOT NULL,
              iteration INTEGER DEFAULT 1,
              input_tokens INTEGER DEFAULT 0,
              cached_input_tokens INTEGER DEFAULT 0,
              output_tokens INTEGER DEFAULT 0,
              reasoning_output_tokens INTEGER DEFAULT 0,
              total_tokens INTEGER DEFAULT 0,
              duration_ms INTEGER DEFAULT 0,
              exit_code INTEGER DEFAULT 0,
              recorded_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO agent_calls SELECT * FROM agent_calls_strict"
        )
        conn.execute("DROP TABLE agent_calls_strict")
        # Insert a genuinely orphan row with run_id IS NULL.
        conn.execute(
            """
            INSERT INTO agent_calls (
                run_id, bead_id, phase_label, agent_label, model,
                total_tokens, recorded_at
            ) VALUES (NULL, 'ORPHAN-BEAD', 'impl', 'orphan', 'claude-sonnet-4-5',
                      999, ?)
            """,
            (datetime.now(timezone.utc).isoformat(),),
        )
        conn.commit()
    finally:
        conn.close()

    # Rolling up a VALID run must now log a visible warning about the orphan
    # rows — they must not be silently dropped per AK.
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="metrics"):
        rollup_run(valid_run, db_path=db)

    messages = " ".join(rec.getMessage().lower() for rec in caplog.records)
    assert "orphan" in messages or "null run_id" in messages or "unattributed" in messages, (
        f"Expected a visible warning about orphan/null-run_id agent_calls, got: {caplog.records}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
