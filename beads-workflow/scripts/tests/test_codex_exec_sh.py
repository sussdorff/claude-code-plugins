#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["pytest>=8.0"]
# ///
"""
Tests for codex-exec.sh — verifies turn.completed token capture via metrics.insert_agent_call().

Three required assertions (tested in test_shell_script_writes_db):
  1. agent_calls row is created (COUNT == 1)
  2. Row has total_tokens > 0, input_tokens > 0, output_tokens > 0
  3. Before rollup: bead_runs.codex_total_tokens == 0;
     after rollup_run(): codex_total_tokens == total_tokens from inserted row
"""

import os
import sqlite3
import stat
import subprocess
import sys
from pathlib import Path

import pytest

# Resolve lib/orchestrator on sys.path regardless of working directory
_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "beads-workflow" / "lib" / "orchestrator"))

from metrics import get_run, rollup_run, start_run

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
_CODEX_EXEC = _SCRIPTS_DIR / "codex-exec.sh"
_METRICS_DIR = str(_REPO_ROOT / "beads-workflow" / "lib" / "orchestrator")


# ---------------------------------------------------------------------------
# Helper: create a mock 'codex' binary that emits a known turn.completed event
# ---------------------------------------------------------------------------

def _make_mock_codex(bin_dir: Path, *, exit_code: int = 0, sleep_secs: float = 0) -> Path:
    """Write a mock codex binary to bin_dir and return bin_dir.

    If sleep_secs > 0, the mock sleeps that many seconds BEFORE emitting any
    output (used to simulate a hang for the timeout test).
    """
    bin_dir.mkdir(parents=True, exist_ok=True)
    mock = bin_dir / "codex"
    sleep_line = f"sleep {sleep_secs}" if sleep_secs > 0 else ""
    mock.write_text(
        f"""#!/usr/bin/env bash
# Mock codex — ignores all arguments, emits known JSON events
{sleep_line}
echo '{{"type":"thread.started","thread_id":"mock-thread"}}'
echo '{{"type":"turn.started"}}'
echo '{{"type":"item.completed","item":{{"id":"item_0","type":"agent_message","text":"mock done"}}}}'
echo '{{"type":"turn.completed","usage":{{"input_tokens":1000,"cached_input_tokens":200,"output_tokens":500}}}}'
exit {exit_code}
"""
    )
    mock.chmod(mock.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return bin_dir


def _make_mock_config(config_dir: Path, model: str = "codex") -> Path:
    """Write a minimal codex config.toml with a known model and return its path."""
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.toml"
    config_file.write_text(f'model = "{model}"\n')
    return config_file


def _env_for_script(
    *,
    run_id: str,
    db: Path,
    mock_bin_dir: Path,
    codex_config: Path | None = None,
    bead_id: str = "TEST-CCP-2vo.3",
    phase_label: str = "codex-review",
    iteration: str = "1",
    wave_id: str = "",
) -> dict:
    """Build an environment dict for running codex-exec.sh."""
    env = os.environ.copy()
    env["PATH"] = f"{mock_bin_dir}:{env.get('PATH', '')}"
    env["RUN_ID"] = run_id
    env["BEAD_ID"] = bead_id
    env["PHASE_LABEL"] = phase_label
    env["ITERATION"] = iteration
    env["METRICS_DB_PATH"] = str(db)
    if codex_config is not None:
        env["CODEX_CONFIG_PATH"] = str(codex_config)
    if wave_id:
        env["WAVE_ID"] = wave_id
    else:
        env.pop("WAVE_ID", None)
    return env


# ---------------------------------------------------------------------------
# Main happy-path integration test (three required assertions)
# ---------------------------------------------------------------------------

def test_shell_script_writes_db(tmp_path: Path) -> None:
    """
    Runs codex-exec.sh with a mock codex binary and verifies:
      1. Exactly one agent_calls row is written for the run_id
      2. The row has total_tokens > 0, input_tokens > 0, output_tokens > 0
      3. Before rollup: codex_total_tokens == 0;
         after rollup_run(): codex_total_tokens == total_tokens from the row
    """
    db = tmp_path / "metrics.db"
    run_id = start_run("TEST-CCP-2vo.3", mode="quick-fix", db_path=db)

    # Pre-condition check (part of assertion 3)
    run_before = get_run(run_id, db_path=db)
    assert run_before["codex_total_tokens"] == 0, (
        "Pre-condition failed: codex_total_tokens must be 0 before rollup"
    )

    mock_dir = _make_mock_codex(tmp_path / "mock_bin")
    # Use model="gpt-5.4" to exercise the normalization path: the script must
    # prefix it to "codex/gpt-5.4" so rollup_run's filter (model LIKE '%codex%') matches.
    codex_config = _make_mock_config(tmp_path / "codex_cfg", model="gpt-5.4")
    env = _env_for_script(run_id=run_id, db=db, mock_bin_dir=mock_dir, codex_config=codex_config)

    result = subprocess.run(
        ["bash", str(_CODEX_EXEC)],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"codex-exec.sh exited {result.returncode}\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )

    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row

    # Assertion 1: exactly one row for this run_id
    count = conn.execute(
        "SELECT COUNT(*) FROM agent_calls WHERE run_id = ?", (run_id,)
    ).fetchone()[0]
    assert count == 1, f"Expected 1 agent_calls row, got {count}"

    # Assertion 2: token fields are positive
    row = conn.execute(
        "SELECT total_tokens, input_tokens, output_tokens FROM agent_calls WHERE run_id = ?",
        (run_id,),
    ).fetchone()
    conn.close()

    total_tokens = row["total_tokens"]
    input_tokens = row["input_tokens"]
    output_tokens = row["output_tokens"]

    assert total_tokens > 0, f"total_tokens should be > 0, got {total_tokens}"
    assert input_tokens > 0, f"input_tokens should be > 0, got {input_tokens}"
    assert output_tokens > 0, f"output_tokens should be > 0, got {output_tokens}"

    # Project convention: total = input + cached_input + output + reasoning (all additive).
    # The mock emits: input=1000, cached=200, output=500, reasoning=0 → total = 1700
    assert input_tokens == 1000
    assert output_tokens == 500
    assert total_tokens == 1700, f"Expected 1700 (1000+200+500), got {total_tokens}"

    # Assertion 3: rollup propagates codex_total_tokens
    rollup_run(run_id, db_path=db)
    run_after = get_run(run_id, db_path=db)
    assert run_after["codex_total_tokens"] == total_tokens, (
        f"After rollup: expected codex_total_tokens={total_tokens}, "
        f"got {run_after['codex_total_tokens']}"
    )


# ---------------------------------------------------------------------------
# Degraded mode: missing RUN_ID → codex still runs, metrics skipped
# ---------------------------------------------------------------------------

def test_missing_run_id_skips_metrics_but_runs_codex(tmp_path: Path) -> None:
    """
    Missing RUN_ID must NOT abort — codex runs, metrics recording is skipped.
    Verifies:
      1. Exit code 0 (codex ran successfully)
      2. No agent_calls row written to any DB
      3. WARNING (not ERROR) referencing RUN_ID appears in stderr
    """
    db = tmp_path / "metrics.db"
    mock_dir = _make_mock_codex(tmp_path / "mock_bin")
    codex_config = _make_mock_config(tmp_path / "codex_cfg")

    env = os.environ.copy()
    env.pop("RUN_ID", None)
    env["BEAD_ID"] = "TEST-CCP-2vo.3"
    env["PHASE_LABEL"] = "codex-review"
    env["PATH"] = f"{mock_dir}:{env.get('PATH', '')}"
    env["METRICS_DB_PATH"] = str(db)
    env["CODEX_CONFIG_PATH"] = str(codex_config)

    result = subprocess.run(
        ["bash", str(_CODEX_EXEC)],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Expected exit 0 when RUN_ID is missing (degraded mode), got {result.returncode}\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert "WARNING" in result.stderr and "RUN_ID" in result.stderr, (
        f"Expected WARNING about RUN_ID in stderr, got: {result.stderr!r}"
    )
    # No DB file should have been created (metrics skipped entirely)
    assert not db.exists(), (
        "metrics.db should not exist when metrics recording is skipped"
    )


# ---------------------------------------------------------------------------
# Error case: missing PHASE_LABEL → non-zero exit
# ---------------------------------------------------------------------------

def test_missing_phase_label_exits_nonzero(tmp_path: Path) -> None:
    """Missing PHASE_LABEL must cause non-zero exit."""
    env = os.environ.copy()
    env["RUN_ID"] = "some-run-id"
    env["BEAD_ID"] = "TEST-CCP-2vo.3"
    env.pop("PHASE_LABEL", None)

    result = subprocess.run(
        ["bash", str(_CODEX_EXEC)],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, (
        "Expected non-zero exit when PHASE_LABEL is missing, got 0"
    )
    assert "PHASE_LABEL" in result.stderr, (
        f"Expected 'PHASE_LABEL' in stderr, got: {result.stderr!r}"
    )


# ---------------------------------------------------------------------------
# Error case: Python metrics recording failure → non-zero exit
# ---------------------------------------------------------------------------

def test_python_metrics_failure_exits_nonzero(tmp_path: Path) -> None:
    """
    When the Python heredoc fails (e.g. run_id not registered in bead_runs),
    codex-exec.sh must exit non-zero and print an error to stderr.

    We pass a RUN_ID that was never start_run()'d so insert_agent_call() raises
    ValueError, which causes Python to exit non-zero, which the shell captures
    and re-raises via the PYTHON_EXIT guard.
    """
    import uuid

    db = tmp_path / "metrics.db"
    # Initialise the DB (creates tables) but do NOT call start_run — run_id unknown.
    # We do this by importing init_db directly.
    from metrics import init_db  # noqa: PLC0415

    conn = init_db(db)
    conn.close()

    unknown_run_id = str(uuid.uuid4())
    mock_dir = _make_mock_codex(tmp_path / "mock_bin")
    codex_config = _make_mock_config(tmp_path / "codex_cfg", model="gpt-5.4")
    env = _env_for_script(
        run_id=unknown_run_id,
        db=db,
        mock_bin_dir=mock_dir,
        codex_config=codex_config,
    )
    env["METRICS_DIR_OVERRIDE"] = _METRICS_DIR

    result = subprocess.run(
        ["bash", str(_CODEX_EXEC)],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, (
        f"Expected non-zero exit when metrics recording fails, got 0\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert "ERROR" in result.stderr, (
        f"Expected 'ERROR' in stderr, got: {result.stderr!r}"
    )


# ---------------------------------------------------------------------------
# Regression test (CCP-dzp): timeout must propagate as non-zero exit
# ---------------------------------------------------------------------------


def test_timeout_exits_nonzero(tmp_path: Path) -> None:
    """
    When codex hangs longer than CODEX_EXEC_TIMEOUT, codex-exec.sh must exit
    non-zero (specifically 124 from the `timeout` utility). Without this, a
    stalled codex could be reported as a clean exit, masking a false-green.

    Skipped if neither `timeout` nor `gtimeout` is available on PATH.
    """
    import shutil

    if not (shutil.which("timeout") or shutil.which("gtimeout")):
        pytest.skip("Neither 'timeout' nor 'gtimeout' is available on this system")

    db = tmp_path / "metrics.db"
    run_id = start_run("TEST-CCP-dzp.timeout", mode="quick-fix", db_path=db)

    # Mock sleeps 5s; timeout fires at 1s → must trigger.
    mock_dir = _make_mock_codex(tmp_path / "mock_bin", sleep_secs=5)
    codex_config = _make_mock_config(tmp_path / "codex_cfg", model="gpt-5.4")
    env = _env_for_script(
        run_id=run_id, db=db, mock_bin_dir=mock_dir, codex_config=codex_config
    )
    env["CODEX_EXEC_TIMEOUT"] = "1"

    result = subprocess.run(
        ["bash", str(_CODEX_EXEC)],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,  # test safety net — must not hang
    )
    assert result.returncode != 0, (
        f"Expected non-zero exit on timeout, got {result.returncode}\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    # `timeout` utility returns 124 when SIGTERM fires on timeout; that's the
    # contract we want flowing through the wrapper.
    assert result.returncode == 124, (
        f"Expected exit code 124 (timeout), got {result.returncode}\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
