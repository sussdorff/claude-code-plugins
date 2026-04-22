#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["pytest>=8.0"]
# ///
"""
Unit tests for beads-workflow/scripts/wave-poll.py
RED phase — tests will fail until wave-poll.py is created.

Tests use mocked wave-completion.sh to exercise all verdict branches:
  - complete
  - needs_intervention/stuck (via stalls array)
  - needs_intervention/stuck (via elapsed hours on stragglers)
  - needs_intervention/ambiguous (exit code 2)
  - needs_intervention/ambiguous (invalid JSON)
  - needs_intervention/pane-error (via cmux mock)
  - needs_intervention/review-loop (via cmux mock)
"""

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

# Locate wave-poll.py relative to this test file
_REPO_ROOT = Path(__file__).resolve().parents[3]
_WAVE_POLL = _REPO_ROOT / "beads-workflow" / "scripts" / "wave-poll.py"


def _make_mock_completion(tmp_path: Path, name: str, stdout: str, exit_code: int) -> Path:
    """Write a mock wave-completion.sh that emits controlled output."""
    script = tmp_path / f"wave-completion-{name}.sh"
    script.write_text(
        f"#!/usr/bin/env bash\n"
        f"echo '{stdout}'\n"
        f"exit {exit_code}\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return script


def _make_wave_config(tmp_path: Path, beads: list[dict] | None = None) -> Path:
    """Write a minimal wave config JSON."""
    if beads is None:
        beads = [{"id": "TEST-aaa", "surface": "surface:99"}]
    config = tmp_path / "wave-config.json"
    config.write_text(json.dumps({
        "wave_id": "test-wave-001",
        "dispatch_time": "2026-04-21T08:00:00",
        "beads": beads,
    }))
    return config


def _run_poll(
    tmp_path: Path,
    wave_config: Path,
    completion_script: Path,
    extra_env: dict | None = None,
    extra_args: list[str] | None = None,
) -> tuple[int, dict | None]:
    """
    Run wave-poll.py and return (returncode, parsed_verdict_or_None).

    Uses WAVE_COMPLETION_OVERRIDE env var to inject the mock script,
    plus --poll-interval 0 to skip sleeping, --stuck-hours 0 to
    trigger stuck detection immediately.
    """
    env = {**os.environ, "WAVE_COMPLETION_OVERRIDE": str(completion_script)}
    if extra_env:
        env.update(extra_env)

    args = [
        sys.executable,
        str(_WAVE_POLL),
        "--config", str(wave_config),
        "--poll-interval", "0",
        "--stuck-hours", "4",
        "--review-max", "3",
    ]
    if extra_args:
        args.extend(extra_args)

    result = subprocess.run(args, capture_output=True, text=True, env=env)
    try:
        verdict = json.loads(result.stdout.strip())
    except (json.JSONDecodeError, ValueError):
        verdict = None
    return result.returncode, verdict


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_wave_poll_exists() -> None:
    """wave-poll.py must exist at the expected path."""
    assert _WAVE_POLL.exists(), f"wave-poll.py not found at {_WAVE_POLL}"


def _check_envelope(result: dict | None) -> None:
    """Assert the result is a valid execution-result envelope."""
    assert result is not None, "Expected JSON output"
    assert result["status"] in {"ok", "warning", "error"}, f"Bad envelope status: {result['status']}"
    assert "data" in result, "Missing 'data' in envelope"
    assert "verdict" in result["data"], "Missing 'data.verdict' in envelope"
    assert "errors" in result, "Missing 'errors' in envelope"
    assert "next_steps" in result, "Missing 'next_steps' in envelope"
    assert "open_items" in result, "Missing 'open_items' in envelope"
    assert "meta" in result, "Missing 'meta' in envelope"
    assert "summary" in result, "Missing 'summary' in envelope"


def test_verdict_complete(tmp_path: Path) -> None:
    """wave-poll.py returns ok envelope with complete verdict when wave-completion.sh reports complete=true."""
    config = _make_wave_config(tmp_path)
    script = _make_mock_completion(
        tmp_path, "complete",
        json.dumps({
            "complete": True,
            "all_beads_closed": True,
            "all_surfaces_idle": True,
            "stragglers": [],
            "unclosed_follow_ups": [],
            "stalls": [],
        }),
        0,
    )
    rc, result = _run_poll(tmp_path, config, script)
    assert rc == 0, f"Expected exit 0, got {rc}"
    _check_envelope(result)
    assert result["status"] == "ok"
    verdict = result["data"]["verdict"]
    assert verdict["status"] == "complete"
    assert "summary" in verdict
    assert "polls_run" in verdict["summary"]


def test_verdict_stuck_via_stalls(tmp_path: Path) -> None:
    """wave-poll.py returns warning envelope with needs_intervention/stuck when stalls array is non-empty."""
    config = _make_wave_config(tmp_path)
    script = _make_mock_completion(
        tmp_path, "stalls",
        json.dumps({
            "complete": False,
            "all_beads_closed": False,
            "all_surfaces_idle": False,
            "stragglers": [{"id": "TEST-aaa", "bd_status": "in_progress", "surface_idle": True}],
            "unclosed_follow_ups": [],
            "stalls": [{"id": "TEST-aaa", "detected_at": "2026-04-21T09:00:00Z", "elapsed_minutes": 65}],
        }),
        1,
    )
    rc, result = _run_poll(tmp_path, config, script)
    assert rc == 0
    _check_envelope(result)
    assert result["status"] == "warning"
    verdict = result["data"]["verdict"]
    assert verdict["status"] == "needs_intervention"
    assert verdict["reason"] == "stuck"
    assert verdict["bead_id"] == "TEST-aaa"


def test_verdict_ambiguous_exit2(tmp_path: Path) -> None:
    """wave-poll.py returns error envelope with needs_intervention/ambiguous when exit code is 2."""
    config = _make_wave_config(tmp_path)
    script = _make_mock_completion(tmp_path, "exit2", "", 2)
    rc, result = _run_poll(tmp_path, config, script)
    assert rc == 0
    _check_envelope(result)
    assert result["status"] == "error"
    verdict = result["data"]["verdict"]
    assert verdict["status"] == "needs_intervention"
    assert verdict["reason"] == "ambiguous"
    assert verdict["bead_id"] is None


def test_verdict_ambiguous_invalid_json(tmp_path: Path) -> None:
    """wave-poll.py returns error envelope with needs_intervention/ambiguous when output is not JSON."""
    config = _make_wave_config(tmp_path)
    script = _make_mock_completion(tmp_path, "badjson", "this is not json", 0)
    rc, result = _run_poll(tmp_path, config, script)
    assert rc == 0
    _check_envelope(result)
    assert result["status"] == "error"
    verdict = result["data"]["verdict"]
    assert verdict["status"] == "needs_intervention"
    assert verdict["reason"] == "ambiguous"


def test_verdict_ambiguous_missing_config(tmp_path: Path) -> None:
    """wave-poll.py returns error envelope with needs_intervention/ambiguous when config file is missing."""
    missing_config = tmp_path / "nonexistent-config.json"
    script = _make_mock_completion(tmp_path, "missing", "{}", 0)

    proc = subprocess.run(
        [sys.executable, str(_WAVE_POLL),
         "--config", str(missing_config),
         "--poll-interval", "0"],
        capture_output=True, text=True,
        env={**os.environ, "WAVE_COMPLETION_OVERRIDE": str(script)},
    )
    result = json.loads(proc.stdout.strip())
    _check_envelope(result)
    assert result["status"] == "error"
    verdict = result["data"]["verdict"]
    assert verdict["status"] == "needs_intervention"
    assert verdict["reason"] == "ambiguous"


def test_cli_args_parsed(tmp_path: Path) -> None:
    """wave-poll.py accepts --config, --stuck-hours, --review-max, --poll-interval."""
    config = _make_wave_config(tmp_path)
    script = _make_mock_completion(
        tmp_path, "cli",
        json.dumps({"complete": True, "stragglers": [], "stalls": []}),
        0,
    )
    rc, result = _run_poll(
        tmp_path, config, script,
        extra_args=["--stuck-hours", "2", "--review-max", "5"],
    )
    assert rc == 0
    _check_envelope(result)
    assert result["data"]["verdict"]["status"] == "complete"


def test_complete_elapsed_minutes_is_integer(tmp_path: Path) -> None:
    """The complete verdict must include an integer elapsed_minutes field (not '?')."""
    config = _make_wave_config(tmp_path)
    script = _make_mock_completion(
        tmp_path, "elapsed",
        json.dumps({"complete": True, "stragglers": [], "stalls": []}),
        0,
    )
    rc, result = _run_poll(tmp_path, config, script)
    assert rc == 0
    _check_envelope(result)
    verdict = result["data"]["verdict"]
    assert verdict["status"] == "complete"
    em = verdict["summary"]["elapsed_minutes"]
    assert isinstance(em, int), f"elapsed_minutes should be int, got {type(em).__name__}: {em!r}"


def test_stuck_by_hours(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """wave-poll.py returns stuck when bd show reports an old Updated date."""
    # Wave completes=False with one in_progress straggler, no stalls
    config = _make_wave_config(tmp_path, beads=[{"id": "TEST-bbb", "surface": "surface:1"}])
    completion_output = json.dumps({
        "complete": False,
        "all_beads_closed": False,
        "all_surfaces_idle": False,
        "stragglers": [{"id": "TEST-bbb", "bd_status": "in_progress", "surface_idle": True}],
        "unclosed_follow_ups": [],
        "stalls": [],
    })
    completion_script = _make_mock_completion(tmp_path, "stuck-hours", completion_output, 0)

    # Mock bd binary: outputs "Updated: 2020-01-01" (far in the past)
    mock_bd = tmp_path / "bd"
    mock_bd.write_text("#!/usr/bin/env bash\necho 'Updated: 2020-01-01'\n")
    mock_bd.chmod(mock_bd.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    # Mock cmux so pane checks are silent (returns empty)
    mock_cmux = tmp_path / "cmux"
    mock_cmux.write_text("#!/usr/bin/env bash\nexit 0\n")
    mock_cmux.chmod(mock_cmux.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    original_path = os.environ.get("PATH", "")
    monkeypatch.setenv("PATH", f"{tmp_path}:{original_path}")

    rc, result = _run_poll(
        tmp_path, config, completion_script,
        extra_args=["--stuck-hours", "1"],
    )
    assert rc == 0
    _check_envelope(result)
    assert result["status"] == "warning"
    verdict = result["data"]["verdict"]
    assert verdict["status"] == "needs_intervention"
    assert verdict["reason"] == "stuck"
    assert verdict["bead_id"] == "TEST-bbb"


def test_pane_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """wave-poll.py returns pane-error when cmux read-screen returns an error signal."""
    config = _make_wave_config(tmp_path, beads=[{"id": "TEST-ccc", "surface": "surface:2"}])
    # wave-completion reports nothing terminal
    completion_output = json.dumps({
        "complete": False,
        "all_beads_closed": False,
        "all_surfaces_idle": False,
        "stragglers": [],
        "unclosed_follow_ups": [],
        "stalls": [],
    })
    completion_script = _make_mock_completion(tmp_path, "pane-err", completion_output, 0)

    # Mock cmux: read-screen --lines returns an error line
    mock_cmux = tmp_path / "cmux"
    mock_cmux.write_text(
        "#!/usr/bin/env bash\n"
        "# Return error output for read-screen calls (but not --scrollback)\n"
        'if [[ "$*" == *"--scrollback"* ]]; then\n'
        "  echo ''\n"
        "else\n"
        "  echo 'fatal: something went wrong'\n"
        "fi\n"
        "exit 0\n"
    )
    mock_cmux.chmod(mock_cmux.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    original_path = os.environ.get("PATH", "")
    monkeypatch.setenv("PATH", f"{tmp_path}:{original_path}")

    rc, result = _run_poll(tmp_path, config, completion_script)
    assert rc == 0
    _check_envelope(result)
    assert result["status"] == "warning"
    verdict = result["data"]["verdict"]
    assert verdict["status"] == "needs_intervention"
    assert verdict["reason"] == "pane-error"
    assert verdict["bead_id"] == "TEST-ccc"


def test_review_loop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """wave-poll.py returns review-loop when scrollback has >= review_max review iterations."""
    config = _make_wave_config(tmp_path, beads=[{"id": "TEST-ddd", "surface": "surface:3"}])
    completion_output = json.dumps({
        "complete": False,
        "all_beads_closed": False,
        "all_surfaces_idle": False,
        "stragglers": [],
        "unclosed_follow_ups": [],
        "stalls": [],
    })
    completion_script = _make_mock_completion(tmp_path, "review-loop", completion_output, 0)

    # Mock cmux: tail read returns empty (no error), scrollback returns 3 review iteration lines
    mock_cmux = tmp_path / "cmux"
    mock_cmux.write_text(
        "#!/usr/bin/env bash\n"
        'if [[ "$*" == *"--scrollback"* ]]; then\n'
        "  echo 'Review iteration 1'\n"
        "  echo 'Review iteration 2'\n"
        "  echo 'Review iteration 3'\n"
        "else\n"
        "  echo ''\n"
        "fi\n"
        "exit 0\n"
    )
    mock_cmux.chmod(mock_cmux.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    original_path = os.environ.get("PATH", "")
    monkeypatch.setenv("PATH", f"{tmp_path}:{original_path}")

    rc, result = _run_poll(
        tmp_path, config, completion_script,
        extra_args=["--review-max", "3"],
    )
    assert rc == 0
    _check_envelope(result)
    assert result["status"] == "warning"
    verdict = result["data"]["verdict"]
    assert verdict["status"] == "needs_intervention"
    assert verdict["reason"] == "review-loop"
    assert verdict["bead_id"] == "TEST-ddd"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
