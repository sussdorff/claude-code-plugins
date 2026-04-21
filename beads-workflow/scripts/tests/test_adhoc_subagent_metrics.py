#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["pytest>=8.0"]
# ///
"""
Tests for the SubagentStop hook: log-adhoc-subagent-metrics.py

Covers:
1. Happy path: no env vars → one adhoc row written
2. Orchestrator context: CCP_ORCHESTRATOR_RUN_ID set → no write
3. Off-switch: CCP_NO_SUBAGENT_METRICS=1 → no write
4. Malformed payload: missing fields → coerce to 0, still write
5. Missing subagent_type → agent_label='unknown'
6. DB locked/unwritable → exit 0, no crash
7. Concurrency: two payloads → two distinct rows with different run_ids
8. Overhead: < 50ms
"""

import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_HOOK_PATH = Path.home() / ".claude" / "hooks" / "log-adhoc-subagent-metrics.py"
sys.path.insert(0, str(_REPO_ROOT / "beads-workflow" / "lib" / "orchestrator"))
from metrics import init_db  # noqa: E402

import pytest


def _run_hook(payload: dict, env: dict | None = None, db_path: Path | None = None) -> subprocess.CompletedProcess:
    """Run the hook script with the given payload and environment."""
    environment = os.environ.copy()
    # Remove orchestrator / off-switch vars by default (clean environment)
    environment.pop("CCP_ORCHESTRATOR_RUN_ID", None)
    environment.pop("CCP_NO_SUBAGENT_METRICS", None)
    if env:
        environment.update(env)
    if db_path:
        environment["CCP_METRICS_DB_PATH"] = str(db_path)

    result = subprocess.run(
        ["python3", str(_HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=environment,
    )
    return result


def _make_payload(**overrides) -> dict:
    """Create a standard SubagentStop payload."""
    base = {
        "hook_event_name": "SubagentStop",
        "session_id": "test-session-123",
        "subagent_type": "impl-sonnet",
        "model": "claude-sonnet-4-6",
        "total_tokens": 5000,
        "input_tokens": 3000,
        "cached_input_tokens": 500,
        "output_tokens": 1500,
        "reasoning_output_tokens": 0,
        "duration_ms": 12345,
        "exit_code": 0,
    }
    base.update(overrides)
    return base


def _count_adhoc_rows(db_path: Path) -> list[sqlite3.Row]:
    """Return all adhoc rows from agent_calls."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM agent_calls WHERE phase_label = 'adhoc'"
        ).fetchall()
    finally:
        conn.close()
    return rows


# ---------------------------------------------------------------------------
# AK1 + AK2: Happy path — hook exists and writes one row
# ---------------------------------------------------------------------------

def test_hook_file_exists() -> None:
    """Hook file must exist at the expected path."""
    assert _HOOK_PATH.exists(), f"Hook not found at {_HOOK_PATH}"


def test_happy_path_writes_one_adhoc_row(tmp_path: Path) -> None:
    """No env vars → one adhoc row written with correct fields."""
    db = tmp_path / "metrics.db"
    init_db(db)

    payload = _make_payload()
    result = _run_hook(payload, db_path=db)

    assert result.returncode == 0, f"Hook exited {result.returncode}: {result.stderr}"

    rows = _count_adhoc_rows(db)
    assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"

    row = rows[0]
    assert row["phase_label"] == "adhoc"
    assert row["agent_label"] == "impl-sonnet"
    assert row["model"] == "claude-sonnet-4-6"
    assert row["total_tokens"] == 5000
    assert row["input_tokens"] == 3000
    assert row["cached_input_tokens"] == 500
    assert row["output_tokens"] == 1500
    assert row["reasoning_output_tokens"] == 0
    assert row["duration_ms"] == 12345
    assert row["exit_code"] == 0

    # run_id must match adhoc-<uuid> format
    assert re.match(r"^adhoc-[0-9a-f-]{36}$", row["run_id"]), (
        f"run_id '{row['run_id']}' does not match adhoc-<uuid> format"
    )

    # bead_id must be empty string (no parent bead for ad-hoc)
    assert row["bead_id"] == ""


# ---------------------------------------------------------------------------
# AK1: Orchestrator context — CCP_ORCHESTRATOR_RUN_ID set → no write
# ---------------------------------------------------------------------------

def test_orchestrator_run_id_skips_write(tmp_path: Path) -> None:
    """CCP_ORCHESTRATOR_RUN_ID set → hook exits 0 without writing any row."""
    db = tmp_path / "metrics.db"
    init_db(db)

    payload = _make_payload()
    result = _run_hook(payload, env={"CCP_ORCHESTRATOR_RUN_ID": "some-run-id"}, db_path=db)

    assert result.returncode == 0, f"Hook exited {result.returncode}: {result.stderr}"

    rows = _count_adhoc_rows(db)
    assert len(rows) == 0, f"Expected 0 rows, got {len(rows)}"


# ---------------------------------------------------------------------------
# AK6: Off-switch — CCP_NO_SUBAGENT_METRICS=1 → no write
# ---------------------------------------------------------------------------

def test_off_switch_skips_write(tmp_path: Path) -> None:
    """CCP_NO_SUBAGENT_METRICS=1 → hook exits 0 without writing any row."""
    db = tmp_path / "metrics.db"
    init_db(db)

    payload = _make_payload()
    result = _run_hook(payload, env={"CCP_NO_SUBAGENT_METRICS": "1"}, db_path=db)

    assert result.returncode == 0, f"Hook exited {result.returncode}: {result.stderr}"

    rows = _count_adhoc_rows(db)
    assert len(rows) == 0, f"Expected 0 rows, got {len(rows)}"


# ---------------------------------------------------------------------------
# Both env vars set together → no write (CCP_NO_SUBAGENT_METRICS takes priority)
# ---------------------------------------------------------------------------

def test_both_env_vars_set_skips_write(tmp_path: Path) -> None:
    """Both CCP_ORCHESTRATOR_RUN_ID and CCP_NO_SUBAGENT_METRICS set → exit 0, zero rows written."""
    db = tmp_path / "metrics.db"
    init_db(db)

    payload = _make_payload()
    result = _run_hook(
        payload,
        env={"CCP_ORCHESTRATOR_RUN_ID": "rn-xyz", "CCP_NO_SUBAGENT_METRICS": "1"},
        db_path=db,
    )

    assert result.returncode == 0, f"Hook exited {result.returncode}: {result.stderr}"

    rows = _count_adhoc_rows(db)
    assert len(rows) == 0, f"Expected 0 rows when both env vars are set, got {len(rows)}"


# ---------------------------------------------------------------------------
# Malformed payload: missing token fields → coerce to 0
# ---------------------------------------------------------------------------

def test_malformed_payload_coerces_to_zero(tmp_path: Path) -> None:
    """Payload missing token fields → coerce to 0, still write one row."""
    db = tmp_path / "metrics.db"
    init_db(db)

    # Only provide hook_event_name and subagent_type
    payload = {
        "hook_event_name": "SubagentStop",
        "subagent_type": "some-agent",
    }
    result = _run_hook(payload, db_path=db)

    assert result.returncode == 0, f"Hook exited {result.returncode}: {result.stderr}"

    rows = _count_adhoc_rows(db)
    assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"
    row = rows[0]
    assert row["total_tokens"] == 0
    assert row["input_tokens"] == 0
    assert row["output_tokens"] == 0
    assert row["duration_ms"] == 0


# ---------------------------------------------------------------------------
# Missing subagent_type → agent_label='unknown'
# ---------------------------------------------------------------------------

def test_missing_subagent_type_uses_unknown(tmp_path: Path) -> None:
    """Missing subagent_type → agent_label set to 'unknown'."""
    db = tmp_path / "metrics.db"
    init_db(db)

    payload = {
        "hook_event_name": "SubagentStop",
        "model": "claude-sonnet-4-6",
        "total_tokens": 100,
    }
    result = _run_hook(payload, db_path=db)

    assert result.returncode == 0
    rows = _count_adhoc_rows(db)
    assert len(rows) == 1
    assert rows[0]["agent_label"] == "unknown"


# ---------------------------------------------------------------------------
# DB locked/unwritable → exit 0, no crash
# ---------------------------------------------------------------------------

def test_db_locked_exits_zero(tmp_path: Path) -> None:
    """DB locked or unwritable → hook exits 0 (never blocks subagent lifecycle)."""
    db = tmp_path / "metrics.db"
    init_db(db)

    # Lock the DB by holding an exclusive transaction
    conn = sqlite3.connect(str(db))
    conn.execute("BEGIN EXCLUSIVE")

    try:
        payload = _make_payload()
        result = _run_hook(payload, db_path=db)
        assert result.returncode == 0, f"Hook must exit 0 on DB lock, got {result.returncode}: {result.stderr}"
    finally:
        conn.rollback()
        conn.close()


# ---------------------------------------------------------------------------
# Concurrency: two payloads → two distinct rows with different run_ids
# ---------------------------------------------------------------------------

def test_two_payloads_produce_distinct_run_ids(tmp_path: Path) -> None:
    """Two sequential hook calls produce two distinct adhoc rows."""
    db = tmp_path / "metrics.db"
    init_db(db)

    payload1 = _make_payload(subagent_type="agent-a", total_tokens=1000)
    payload2 = _make_payload(subagent_type="agent-b", total_tokens=2000)

    _run_hook(payload1, db_path=db)
    _run_hook(payload2, db_path=db)

    rows = _count_adhoc_rows(db)
    assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"

    run_ids = {row["run_id"] for row in rows}
    assert len(run_ids) == 2, f"run_ids must be distinct, got: {run_ids}"

    agent_labels = {row["agent_label"] for row in rows}
    assert agent_labels == {"agent-a", "agent-b"}


# ---------------------------------------------------------------------------
# AK8: Overhead < 50ms
# ---------------------------------------------------------------------------

def test_hook_overhead_under_50ms(tmp_path: Path) -> None:
    """Hook must complete in under 50ms across 10 trials (non-blocking performance requirement)."""
    db = tmp_path / "metrics.db"
    init_db(db)

    payload = _make_payload()
    elapsed_times = []
    for _ in range(10):
        start = time.perf_counter()
        result = _run_hook(payload, db_path=db)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert result.returncode == 0
        elapsed_times.append(elapsed_ms)

    median_ms = sorted(elapsed_times)[len(elapsed_times) // 2]
    assert median_ms < 50, (
        f"Median hook time {median_ms:.1f}ms exceeds 50ms limit "
        f"(all times: {[f'{t:.1f}' for t in elapsed_times]})"
    )


# ---------------------------------------------------------------------------
# AK5: query_adhoc_report exists and returns correct format
# ---------------------------------------------------------------------------

def test_query_adhoc_report_returns_table(tmp_path: Path) -> None:
    """query_adhoc_report must return a markdown table with adhoc data."""
    from metrics import query_adhoc_report

    db = tmp_path / "metrics.db"
    init_db(db)

    # Write two adhoc rows manually
    payload1 = _make_payload(subagent_type="impl-sonnet", total_tokens=3000)
    payload2 = _make_payload(subagent_type="impl-sonnet", total_tokens=4000)
    payload3 = _make_payload(subagent_type="review-opus", total_tokens=1000)

    _run_hook(payload1, db_path=db)
    _run_hook(payload2, db_path=db)
    _run_hook(payload3, db_path=db)

    report = query_adhoc_report(db_path=db)
    assert "Ad-hoc Agent Usage" in report
    assert "impl-sonnet" in report
    assert "review-opus" in report
    assert "|" in report  # markdown table


def test_query_adhoc_report_empty_db(tmp_path: Path) -> None:
    """query_adhoc_report with no data must return 'No ad-hoc data yet.'"""
    from metrics import query_adhoc_report

    db = tmp_path / "empty.db"
    report = query_adhoc_report(db_path=db)
    assert "No ad-hoc data yet" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
