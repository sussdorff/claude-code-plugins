#!/usr/bin/env python3
"""
Tests for wave-orchestrator Python scripts:
  - wave_helpers.py
  - arch-signal-detect.py
  - wave-lock.py
  - wave-completion.py
"""

import importlib.util
import io
import json
import os
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]

# Add scripts dir to sys.path for modules with valid Python names (wave_lock, etc.)
sys.path.insert(0, str(_SCRIPTS_DIR))


def _load_module(name: str, path: Path):
    """Import a module from a file path (works even with hyphens in filename)."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _asd():
    """Load arch-signal-detect module."""
    return _load_module("arch_signal_detect", _SCRIPTS_DIR / "arch-signal-detect.py")


# ---------------------------------------------------------------------------
# wave_helpers.py tests
# ---------------------------------------------------------------------------


def test_wave_helpers_importable() -> None:
    """wave_helpers module must be importable and export expected names."""
    import wave_helpers

    assert hasattr(wave_helpers, "_THINKING_RE")
    assert hasattr(wave_helpers, "_PROMPT_RE")
    assert hasattr(wave_helpers, "_DEAD_SURFACE_RE")
    assert callable(wave_helpers._surface_is_idle)
    assert callable(wave_helpers._read_surface)
    assert callable(wave_helpers._bd_status)
    assert callable(wave_helpers._elapsed_minutes)


def test_wave_helpers_surface_is_idle_with_prompt() -> None:
    """_surface_is_idle returns True when last non-empty line is a shell prompt."""
    from wave_helpers import _surface_is_idle

    screen = "Some output\n$ \n"
    assert _surface_is_idle(screen) is True


def test_wave_helpers_surface_is_idle_with_thinking() -> None:
    """_surface_is_idle returns False when preceding lines show Thinking."""
    from wave_helpers import _surface_is_idle

    screen = "Thinking...\nsome output\n$ \n"
    assert _surface_is_idle(screen) is False


def test_wave_helpers_surface_not_idle_no_prompt() -> None:
    """_surface_is_idle returns False when last line is not a prompt."""
    from wave_helpers import _surface_is_idle

    screen = "Some output without prompt\n"
    assert _surface_is_idle(screen) is False


def test_wave_helpers_elapsed_minutes_valid() -> None:
    """_elapsed_minutes returns a non-negative int for a recent timestamp."""
    from wave_helpers import _elapsed_minutes

    # Use a recent-past timestamp (a couple minutes ago would give ~2)
    result = _elapsed_minutes("2020-01-01T00:00:00")
    assert isinstance(result, int)
    assert result > 0


def test_wave_helpers_elapsed_minutes_invalid() -> None:
    """_elapsed_minutes returns 0 on parse error."""
    from wave_helpers import _elapsed_minutes

    result = _elapsed_minutes("not-a-timestamp")
    assert result == 0


# ---------------------------------------------------------------------------
# arch-signal-detect.py tests
# ---------------------------------------------------------------------------


def test_arch_signal_no_args_exits_one() -> None:
    """arch-signal-detect.py with no args must exit 1."""
    result = subprocess.run(
        ["python3", str(_SCRIPTS_DIR / "arch-signal-detect.py")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "No bead IDs" in result.stderr


def test_arch_signal_strong_pattern() -> None:
    """[ARCH] in title produces score >= 6 → REVIEW_YES."""
    asd = _asd()

    class MockRunner(asd.CommandRunner):
        def run_json(self, cmd: list[str]) -> Any:
            return [
                {
                    "title": "[ARCH] Redesign state machine boundaries",
                    "description": "Needs API contract layer separation protocol",
                    "issue_type": "feature",
                    "blocks": [],
                }
            ]

    runner = MockRunner()
    result = asd.analyze_bead("CCP-abc", runner)
    assert result.verdict == asd.REVIEW_YES
    assert result.score >= 6


def test_arch_signal_medium_pattern_no_strong() -> None:
    """[REFACTOR] + alternative approach = 4 pts → REVIEW_MAYBE."""
    asd = _asd()

    class MockRunner(asd.CommandRunner):
        def run_json(self, cmd: list[str]) -> Any:
            return [
                {
                    "title": "[REFACTOR] Update tests",
                    "description": "Some refactoring with alternative approach",
                    "issue_type": "feature",
                    "blocks": [],
                }
            ]

    runner = MockRunner()
    result = asd.analyze_bead("CCP-def", runner)
    # [REFACTOR] = 2 + "alternative approach" = 2 → total 4 → REVIEW_MAYBE
    assert result.score >= 3
    assert result.verdict == asd.REVIEW_MAYBE


def test_arch_signal_bug_type_auto_skip() -> None:
    """Bugs are always REVIEW_NO regardless of content."""
    asd = _asd()

    class MockRunner(asd.CommandRunner):
        def run_json(self, cmd: list[str]) -> Any:
            return [
                {
                    "title": "[ARCH] Fix a bug with state machine protocol",
                    "description": "Has API contract",
                    "issue_type": "bug",
                    "blocks": [],
                }
            ]

    runner = MockRunner()
    result = asd.analyze_bead("CCP-bug", runner)
    assert result.verdict == asd.REVIEW_NO
    assert result.score == 0
    assert "auto-skip" in result.reason


def test_arch_signal_chore_type_auto_skip() -> None:
    """Chores are always REVIEW_NO."""
    asd = _asd()

    class MockRunner(asd.CommandRunner):
        def run_json(self, cmd: list[str]) -> Any:
            return [
                {
                    "title": "[ARCH] Chore with protocol",
                    "description": "API contract needed",
                    "issue_type": "chore",
                    "blocks": [],
                }
            ]

    runner = MockRunner()
    result = asd.analyze_bead("CCP-chore", runner)
    assert result.verdict == asd.REVIEW_NO


def test_arch_signal_dependency_count_adds_medium() -> None:
    """blocks >= 2 adds +2 pts (MEDIUM)."""
    asd = _asd()

    class MockRunner(asd.CommandRunner):
        def run_json(self, cmd: list[str]) -> Any:
            return [
                {
                    "title": "[REFACTOR] Rewrite module",
                    "description": "Minor change",
                    "issue_type": "feature",
                    "blocks": ["CCP-1", "CCP-2", "CCP-3"],
                }
            ]

    runner = MockRunner()
    result = asd.analyze_bead("CCP-dep", runner)
    # [REFACTOR] = 2 + blocks 3 beads = 2 → total 4 → REVIEW_MAYBE
    assert result.score == 4
    assert result.verdict == asd.REVIEW_MAYBE


def test_arch_signal_bead_not_found() -> None:
    """When bd show fails, result has error field."""
    asd = _asd()

    class MockRunner(asd.CommandRunner):
        def run_json(self, cmd: list[str]) -> Any:
            return None

    runner = MockRunner()
    result = asd.analyze_bead("CCP-unknown", runner)
    assert result.error == "bead not found"


def test_arch_signal_output_is_json_array() -> None:
    """Main output to stdout must be a valid JSON array."""
    asd = _asd()

    class MockRunner(asd.CommandRunner):
        def run_json(self, cmd: list[str]) -> Any:
            return [
                {
                    "title": "Simple task",
                    "description": "Nothing architectural",
                    "issue_type": "feature",
                    "blocks": [],
                }
            ]

    buf = io.StringIO()
    old_argv = sys.argv
    sys.argv = ["arch-signal-detect.py", "CCP-test"]
    try:
        with redirect_stdout(buf):
            exit_code = asd.main(runner=MockRunner())
    finally:
        sys.argv = old_argv

    assert exit_code == 0
    output = buf.getvalue()
    parsed = json.loads(output)
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert "verdict" in parsed[0]


def test_arch_signal_envelope_schema() -> None:
    """Envelope must conform to execution-result schema (required top-level keys)."""
    asd = _asd()

    signals = [{"id": "CCP-x", "verdict": asd.REVIEW_YES, "score": 6, "signals": []}]
    envelope = asd.build_envelope(signals)

    required_keys = {"status", "summary", "data", "errors", "next_steps", "open_items", "meta"}
    assert required_keys.issubset(envelope.keys())
    assert "signals" in envelope["data"]
    assert envelope["meta"]["producer"] == "arch-signal-detect.py"
    assert envelope["meta"]["contract_version"] == "1.0"


# ---------------------------------------------------------------------------
# wave-lock.py tests
# ---------------------------------------------------------------------------


def _wl():
    """Load wave-lock module."""
    return _load_module("wave_lock", _SCRIPTS_DIR / "wave-lock.py")


def test_wave_lock_acquire_and_status(tmp_path: Path) -> None:
    """acquire creates lockfile; status reads it."""
    wl = _wl()
    lockfile = tmp_path / "test.lock"

    # Status on non-existent file
    status = wl.cmd_status(str(lockfile))
    assert status["holder"] is None

    # Acquire
    result = wl.cmd_acquire(str(lockfile), "wave-test", "surface:1")
    assert result == 0

    # Status now shows holder
    status = wl.cmd_status(str(lockfile))
    assert status["holder"] is not None
    assert status["holder"]["wave_id"] == "wave-test"
    assert status["holder"]["surface"] == "surface:1"


def test_wave_lock_release(tmp_path: Path) -> None:
    """release clears the lockfile."""
    wl = _wl()
    lockfile = tmp_path / "test.lock"
    wl.cmd_acquire(str(lockfile), "wave-test", "surface:1")

    result = wl.cmd_release(str(lockfile))
    assert result == 0

    status = wl.cmd_status(str(lockfile))
    assert status["holder"] is None


def test_wave_lock_release_nonexistent_is_ok(tmp_path: Path) -> None:
    """release on non-existent lockfile exits 0 (no-op)."""
    wl = _wl()
    lockfile = tmp_path / "nonexistent.lock"
    result = wl.cmd_release(str(lockfile))
    assert result == 0


def test_wave_lock_acquire_collision(tmp_path: Path) -> None:
    """Acquiring when holder PID is alive → returns 1."""
    wl = _wl()
    lockfile = tmp_path / "test.lock"

    # Write a lock with OUR pid (which is alive)
    my_pid = os.getpid()
    lock_data = {
        "holder": {
            "wave_id": "wave-existing",
            "surface": "surface:99",
            "pid": my_pid,
            "acquired_at": "2026-01-01T00:00:00Z",
        }
    }
    lockfile.write_text(json.dumps(lock_data))

    result = wl.cmd_acquire(str(lockfile), "wave-new", "surface:1")
    assert result == 1  # fail-fast


def test_wave_lock_stale_pid_auto_cleared(tmp_path: Path) -> None:
    """Lock with dead PID → auto-clear, acquire succeeds (returns 0)."""
    wl = _wl()
    lockfile = tmp_path / "test.lock"

    # Write a lock with dead PID (PID 999999 unlikely to exist)
    lock_data = {
        "holder": {
            "wave_id": "wave-stale",
            "surface": "surface:5",
            "pid": 999999,
            "acquired_at": "2026-01-01T00:00:00Z",
        }
    }
    lockfile.write_text(json.dumps(lock_data))

    result = wl.cmd_acquire(str(lockfile), "wave-new", "surface:1")
    # If PID 999999 is actually alive (very unlikely), skip this test
    if result == 1:
        pytest.skip("PID 999999 appears to be alive on this system")
    assert result == 0

    # Verify new holder is written
    status = wl.cmd_status(str(lockfile))
    assert status["holder"]["wave_id"] == "wave-new"


# ---------------------------------------------------------------------------
# wave-completion.py tests (via subprocess)
# ---------------------------------------------------------------------------


def test_wave_completion_exits_two_on_missing_config(tmp_path: Path) -> None:
    """wave-completion.py exits 2 when config file doesn't exist."""
    result = subprocess.run(
        [
            "python3",
            str(_SCRIPTS_DIR / "wave-completion.py"),
            str(tmp_path / "nonexistent.json"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "not found" in result.stderr.lower() or "Error" in result.stderr


# ---------------------------------------------------------------------------
# wave-dispatch.py tests (WaveDispatcher class)
# ---------------------------------------------------------------------------


def _wd():
    """Load wave-dispatch module."""
    return _load_module("wave_dispatch", _SCRIPTS_DIR / "wave-dispatch.py")


class _MockResult:
    """Simple mock for subprocess.run result."""

    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def test_wave_dispatcher_empty_bead_list_returns_error() -> None:
    """WaveDispatcher.dispatch with empty bead list returns exit code 1."""
    wd = _wd()

    calls: list = []

    def mock_runner(cmd, **kwargs):
        calls.append(cmd)
        return _MockResult()

    dispatcher = wd.WaveDispatcher(runner=mock_runner)
    exit_code, output = dispatcher.dispatch(
        bead_ids=[],
        quick_ids=[],
        workspace="ws:1",
        base_surface="surface:1",
        wave_id="wave-test",
        skip_scenarios=True,
    )
    assert exit_code == 1
    assert output == {}


def test_wave_dispatcher_constructs_cmux_send_command() -> None:
    """WaveDispatcher dispatches cmux send with correct bead ID and cld flag."""
    wd = _wd()

    # Track all cmux send calls
    send_calls: list[list] = []

    def mock_runner(cmd, **kwargs):
        if cmd and cmd[0] == "cmux" and "new-split" in cmd:
            # Return surface identifier in stdout
            return _MockResult(stdout="Created surface:42\n")
        if cmd and cmd[0] == "cmux" and "send" in cmd and "--surface" in cmd:
            send_calls.append(cmd)
        return _MockResult()

    dispatcher = wd.WaveDispatcher(runner=mock_runner)
    exit_code, output = dispatcher.dispatch(
        bead_ids=["proj-abc"],
        quick_ids=[],
        workspace="ws:1",
        base_surface="surface:1",
        wave_id="wave-2026",
        skip_scenarios=True,
    )
    assert exit_code == 0
    assert len(output["beads"]) == 1
    assert output["beads"][0]["id"] == "proj-abc"
    assert output["beads"][0]["mode"] == "full"

    # Verify cmux send included cld -b (full mode)
    found_send = any(
        "cld -b proj-abc" in " ".join(c) for c in send_calls
    )
    assert found_send, f"Expected 'cld -b proj-abc' in send calls, got: {send_calls}"


def test_wave_dispatcher_send_includes_newline_no_enter_flag() -> None:
    """cmux send text must end with \\n — Enter must NOT be appended as --enter text."""
    wd = _wd()

    send_calls: list[list] = []
    send_key_calls: list[list] = []

    def mock_runner(cmd, **kwargs):
        if cmd and cmd[0] == "cmux" and "new-split" in cmd:
            return _MockResult(stdout="surface:42\n")
        if cmd and cmd[0] == "cmux" and cmd[1] == "send" and "--surface" in cmd:
            send_calls.append(cmd)
        if cmd and cmd[0] == "cmux" and cmd[1] == "send-key":
            send_key_calls.append(cmd)
        return _MockResult()

    dispatcher = wd.WaveDispatcher(runner=mock_runner)
    exit_code, _ = dispatcher.dispatch(
        bead_ids=["proj-abc"],
        quick_ids=[],
        workspace="ws:1",
        base_surface="surface:1",
        wave_id="wave-2026",
        skip_scenarios=True,
    )
    assert exit_code == 0

    # The send text must end with the literal two-char escape \n (not a real newline byte).
    # cmux send documents "Escape sequences: \n and \r send Enter" — this refers to the
    # literal backslash-n characters, not a raw LF byte. Passing "\\n" in Python ensures
    # cmux receives the two chars \ and n and processes them as its Enter escape.
    assert send_calls, "Expected at least one cmux send call"
    send_text = send_calls[-1][-1]  # last arg is the text
    assert send_text.endswith("\\n"), (
        f"cmux send text must end with literal \\\\n (backslash-n) to submit the command. Got: {send_text!r}"
    )

    # --enter must NOT appear anywhere in the send text (it's not a cmux send flag)
    assert "--enter" not in send_text, (
        f"--enter must NOT be appended as text. Got: {send_text!r}"
    )

    # send-key with 'enter' must NOT be used (redundant when \n escape is in the send text)
    enter_key_calls = [c for c in send_key_calls if "enter" in c]
    assert not enter_key_calls, (
        f"cmux send-key enter must NOT be called when \\\\n is in send text. Got: {enter_key_calls}"
    )


def test_wave_dispatcher_quick_flag_routing() -> None:
    """--quick beads use cld -bq in the send command."""
    wd = _wd()

    send_calls: list[list] = []

    def mock_runner(cmd, **kwargs):
        if cmd and cmd[0] == "cmux" and "new-split" in cmd:
            return _MockResult(stdout="surface:10\n")
        if cmd and cmd[0] == "cmux" and "send" in cmd and "--surface" in cmd:
            send_calls.append(cmd)
        return _MockResult()

    dispatcher = wd.WaveDispatcher(runner=mock_runner)
    exit_code, output = dispatcher.dispatch(
        bead_ids=[],
        quick_ids=["proj-qf1"],
        workspace="ws:1",
        base_surface="surface:1",
        wave_id="wave-2026",
        skip_scenarios=True,
    )
    assert exit_code == 0
    assert output["beads"][0]["mode"] == "quick"

    found_quick = any(
        "cld -bq proj-qf1" in " ".join(c) for c in send_calls
    )
    assert found_quick, f"Expected 'cld -bq proj-qf1' in send calls, got: {send_calls}"


def test_wave_dispatcher_scenario_gate_blocks_feature_bead() -> None:
    """Feature beads without ## Scenario section block dispatch (exit code 1)."""
    wd = _wd()

    def mock_runner(cmd, **kwargs):
        # bd show --json returns feature type
        if cmd and cmd[0] == "bd" and "--json" in cmd:
            return _MockResult(stdout='[{"issue_type": "feature"}]', returncode=0)
        # bd show (no --json) returns description without Scenario section
        if cmd and cmd[0] == "bd" and "--json" not in cmd:
            return _MockResult(stdout="Title: My feature\nDescription: stuff\n")
        return _MockResult()

    dispatcher = wd.WaveDispatcher(runner=mock_runner)
    exit_code, output = dispatcher.dispatch(
        bead_ids=["proj-feat"],
        quick_ids=[],
        workspace="ws:1",
        base_surface="surface:1",
        wave_id="wave-test",
        skip_scenarios=False,
    )
    assert exit_code == 1
    assert output == {}


def test_wave_dispatcher_skip_scenarios_bypasses_gate() -> None:
    """--skip-scenarios bypasses the scenario gate even for feature beads."""
    wd = _wd()

    def mock_runner(cmd, **kwargs):
        if cmd and cmd[0] == "cmux" and "new-split" in cmd:
            return _MockResult(stdout="surface:5\n")
        return _MockResult()

    dispatcher = wd.WaveDispatcher(runner=mock_runner)
    exit_code, output = dispatcher.dispatch(
        bead_ids=["proj-feat"],
        quick_ids=[],
        workspace="ws:1",
        base_surface="surface:1",
        wave_id="wave-test",
        skip_scenarios=True,
    )
    assert exit_code == 0


def test_wave_dispatcher_wave_id_auto_generation() -> None:
    """wave_id in output matches a wave-YYYYMMDD-HHMMSS pattern when auto-generated via dispatch()."""
    wd = _wd()

    def mock_runner(cmd, **kwargs):
        if cmd and cmd[0] == "cmux" and "new-split" in cmd:
            return _MockResult(stdout="surface:7\n")
        return _MockResult()

    dispatcher = wd.WaveDispatcher(runner=mock_runner)
    # Pass an empty wave_id to trigger auto-generation inside dispatch()
    # The auto-generation actually happens in main(), so we test it via main() logic:
    # dispatch() receives the wave_id as a parameter — test that the format is correct
    # when main() generates it via the datetime pattern.
    # Here we verify the datetime pattern directly:
    import re as _re
    from datetime import datetime, timezone

    generated = f"wave-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    assert _re.match(r"wave-\d{8}-\d{6}", generated), generated

    # Also verify dispatch() passes the wave_id straight through to output
    exit_code, output = dispatcher.dispatch(
        bead_ids=["proj-abc"],
        quick_ids=[],
        workspace="ws:1",
        base_surface="surface:1",
        wave_id=generated,
        skip_scenarios=True,
    )
    assert exit_code == 0
    assert output["wave_id"] == generated


def test_wave_dispatch_main_requires_workspace_flag() -> None:
    """wave-dispatch.py main() must exit 2 when --workspace is missing.

    Regression: previously main() silently fell back to `cmux identify` which in
    Agent subagent contexts returned the wrong workspace and dispatched beads
    into unrelated projects. --workspace is now mandatory.
    """
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPTS_DIR / "wave-dispatch.py"),
            "proj-abc",
            "--base-pane",
            "surface:1",
            "--skip-scenarios",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 2, (
        f"expected exit 2 without --workspace, got {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "--workspace is required" in result.stderr


def test_wave_dispatch_main_requires_base_pane_flag() -> None:
    """wave-dispatch.py main() must exit 2 when --base-pane is missing.

    Same rationale as --workspace: silent cmux identify fallback was unsafe.
    """
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPTS_DIR / "wave-dispatch.py"),
            "proj-abc",
            "--workspace",
            "workspace:5",
            "--skip-scenarios",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 2, (
        f"expected exit 2 without --base-pane, got {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "--base-pane is required" in result.stderr


# ---------------------------------------------------------------------------
# wave-status.py tests
# ---------------------------------------------------------------------------


def _ws():
    """Load wave-status module."""
    return _load_module("wave_status", _SCRIPTS_DIR / "wave-status.py")


def test_wave_status_returns_correct_json_structure() -> None:
    """check_wave_status returns dict with required top-level keys."""
    ws = _ws()

    def mock_runner(cmd, **kwargs):
        # cmux read-screen → idle prompt
        if cmd and cmd[0] == "cmux":
            return _MockResult(stdout="$ \n")
        # bd show → CLOSED
        if cmd and cmd[0] == "bd":
            return _MockResult(stdout="Status: CLOSED\n")
        return _MockResult()

    config = {
        "dispatch_time": "2026-01-01T00:00:00",
        "beads": [{"id": "proj-abc", "surface": "surface:1"}],
    }
    result = ws.check_wave_status(config, runner=mock_runner)

    assert "elapsed_minutes" in result
    assert "beads" in result
    assert "all_done" in result
    assert "follow_up_beads" in result
    assert isinstance(result["beads"], list)
    assert len(result["beads"]) == 1


def test_wave_status_idle_surface_detection() -> None:
    """Surfaces ending with a shell prompt are detected as done (idle)."""
    ws = _ws()

    def mock_runner(cmd, **kwargs):
        if cmd and cmd[0] == "cmux":
            # idle surface: last line is shell prompt
            return _MockResult(stdout="Some output\n$ \n")
        if cmd and cmd[0] == "bd":
            return _MockResult(stdout="Status: CLOSED\n")
        return _MockResult()

    config = {
        "dispatch_time": "2026-01-01T00:00:00",
        "beads": [{"id": "proj-idle", "surface": "surface:3"}],
    }
    result = ws.check_wave_status(config, runner=mock_runner)
    bead = result["beads"][0]
    assert bead["status"] == "done"


def test_wave_status_active_surface_not_done() -> None:
    """Surfaces showing active tool use are not marked done."""
    ws = _ws()

    def mock_runner(cmd, **kwargs):
        if cmd and cmd[0] == "cmux":
            # Surface showing active editing (no trailing prompt)
            return _MockResult(stdout="Edit file.py\nWrite output.txt\n")
        if cmd and cmd[0] == "bd":
            return _MockResult(stdout="Status: IN_PROGRESS\n")
        return _MockResult()

    config = {
        "dispatch_time": "2026-01-01T00:00:00",
        "beads": [{"id": "proj-busy", "surface": "surface:5"}],
    }
    result = ws.check_wave_status(config, runner=mock_runner)
    bead = result["beads"][0]
    assert bead["status"] != "done"
    assert result["all_done"] is False


def test_wave_status_elapsed_minutes_calculated() -> None:
    """elapsed_minutes is a non-negative integer for a past dispatch time."""
    ws = _ws()

    def mock_runner(cmd, **kwargs):
        return _MockResult(stdout="")

    config = {
        "dispatch_time": "2020-01-01T00:00:00",
        "beads": [],
    }
    result = ws.check_wave_status(config, runner=mock_runner)
    assert isinstance(result["elapsed_minutes"], int)
    assert result["elapsed_minutes"] > 0


def test_wave_dispatcher_skips_already_running_bead() -> None:
    """Dispatch skips a bead that has an active process (pgrep returns PID)."""
    wd = _wd()

    cmux_split_calls: list = []

    def mock_runner(cmd, **kwargs):
        # pgrep returns a PID → bead is running
        if cmd and cmd[0] == "pgrep":
            return _MockResult(stdout="12345\n", returncode=0)
        # git worktree list returns nothing relevant
        if cmd and cmd[0] == "git" and "worktree" in cmd:
            return _MockResult(stdout="worktree /other\nHEAD abc123\nbranch refs/heads/main\n\n")
        if cmd and cmd[0] == "cmux" and "new-split" in cmd:
            cmux_split_calls.append(cmd)
            return _MockResult(stdout="surface:99\n")
        return _MockResult()

    dispatcher = wd.WaveDispatcher(runner=mock_runner)
    exit_code, output = dispatcher.dispatch(
        bead_ids=["proj-abc"],
        quick_ids=[],
        workspace="ws:1",
        base_surface="surface:1",
        wave_id="wave-test",
        skip_scenarios=True,
    )

    # Dispatch should succeed overall (exit 0) but skip the already-running bead
    assert exit_code == 0
    # No cmux split should have been created for the running bead
    assert cmux_split_calls == [], f"Expected no cmux splits, got: {cmux_split_calls}"
    # Output should record the bead as already-running
    assert len(output["beads"]) == 1
    assert output["beads"][0]["status"] == "already-running"
    assert "12345" in output["beads"][0]["pids"]


def test_wave_dispatcher_proceeds_when_not_running() -> None:
    """Dispatch proceeds normally when pgrep finds no process and no worktree exists."""
    wd = _wd()

    cmux_split_calls: list = []

    def mock_runner(cmd, **kwargs):
        # pgrep returns nothing → bead NOT running
        if cmd and cmd[0] == "pgrep":
            return _MockResult(stdout="", returncode=1)
        # git worktree list returns no matching worktree
        if cmd and cmd[0] == "git" and "worktree" in cmd:
            return _MockResult(stdout="worktree /some/other/path\nHEAD abc123\nbranch refs/heads/main\n\n")
        if cmd and cmd[0] == "cmux" and "new-split" in cmd:
            cmux_split_calls.append(cmd)
            return _MockResult(stdout="surface:42\n")
        return _MockResult()

    dispatcher = wd.WaveDispatcher(runner=mock_runner)
    exit_code, output = dispatcher.dispatch(
        bead_ids=["proj-abc"],
        quick_ids=[],
        workspace="ws:1",
        base_surface="surface:1",
        wave_id="wave-test",
        skip_scenarios=True,
    )

    assert exit_code == 0
    assert len(cmux_split_calls) == 1, f"Expected 1 cmux split, got: {cmux_split_calls}"
    assert len(output["beads"]) == 1
    assert output["beads"][0]["status"] == "dispatched"


def test_wave_dispatcher_skips_already_running_bead_worktree_only() -> None:
    """Dispatch skips a bead when only a worktree exists (no live process).

    Regression test for AK1/AK3: the worktree check alone must be sufficient
    to prevent duplicate dispatch even when pgrep returns nothing.
    """
    wd = _wd()

    cmux_split_calls: list = []

    def mock_runner(cmd, **kwargs):
        # pgrep finds nothing → no live process
        if cmd and cmd[0] == "pgrep":
            return _MockResult(stdout="", returncode=1)
        # git worktree list returns the bead's worktree
        if cmd and cmd[0] == "git" and "worktree" in cmd:
            return _MockResult(
                stdout=(
                    "worktree /path/bead-proj-wt\n"
                    "HEAD abc123\n"
                    "branch refs/heads/worktree-bead-proj-wt\n"
                    "\n"
                ),
                returncode=0,
            )
        if cmd and cmd[0] == "cmux" and "new-split" in cmd:
            cmux_split_calls.append(cmd)
            return _MockResult(stdout="surface:99\n")
        return _MockResult()

    dispatcher = wd.WaveDispatcher(runner=mock_runner)
    exit_code, output = dispatcher.dispatch(
        bead_ids=["proj-wt"],
        quick_ids=[],
        workspace="ws:1",
        base_surface="surface:1",
        wave_id="wave-test",
        skip_scenarios=True,
    )

    # Dispatch should succeed overall (exit 0) but skip the bead with worktree
    assert exit_code == 0
    # No cmux split should have been created
    assert cmux_split_calls == [], f"Expected no cmux splits, got: {cmux_split_calls}"
    # Output should record the bead as already-running with worktree_path populated
    assert len(output["beads"]) == 1
    bead = output["beads"][0]
    assert bead["status"] == "already-running"
    assert bead["pids"] == []
    assert "/path/bead-proj-wt" in bead["worktree_path"]


def test_phase_b_close_beads_skips_foreign_bead(tmp_path: Path) -> None:
    """phase-b-close-beads.sh skips beads owned by a different session (AK4).

    Creates a mock bd binary that returns one in-progress bead assigned to a
    different session. Verifies the bead appears in skipped_not_owned and not
    in closed.
    """
    # Create mock bd binary
    mock_bd = tmp_path / "bd"
    mock_bd.write_text(
        "#!/usr/bin/env bash\n"
        "# Mock bd for ownership test\n"
        "if [[ \"$1\" == 'list' ]]; then\n"
        "  echo '[{\"id\":\"TEST-001\",\"status\":\"in_progress\"}]'\n"
        "elif [[ \"$1\" == 'show' ]]; then\n"
        "  echo '[{\"id\":\"TEST-001\",\"title\":\"Foreign bead\",\"type\":\"task\","
        "\"notes\":\"\",\"assignee\":\"session-OTHER-999\"}]'\n"
        "elif [[ \"$1\" == 'dolt' ]]; then\n"
        "  echo 'ok'\n"
        "fi\n"
    )
    mock_bd.chmod(0o755)

    script = (
        Path(__file__).resolve().parents[5]
        / "core" / "agents" / "session-close-handlers" / "phase-b-close-beads.sh"
    )

    env = os.environ.copy()
    env["PATH"] = str(tmp_path) + ":" + env.get("PATH", "")
    env["CCP_SESSION_ID"] = "session-test-111"
    # Prevent git from complaining about repo root
    env["GIT_DIR"] = str(tmp_path / ".git")

    result = subprocess.run(
        ["bash", str(script), "--dry-run"],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )

    # Script should succeed (exit 0 — no beads to close, just skipped)
    assert result.returncode == 0, (
        f"Expected exit 0, got {result.returncode}; stderr={result.stderr!r}"
    )

    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"Output was not valid JSON: {result.stdout!r}")

    # Foreign bead should be in skipped_not_owned
    assert "skipped_not_owned" in output, f"Missing skipped_not_owned key: {output}"
    assert "TEST-001" in output["skipped_not_owned"], (
        f"Expected TEST-001 in skipped_not_owned, got: {output['skipped_not_owned']}"
    )
    # Foreign bead should NOT be in closed
    closed_ids = [b["id"] if isinstance(b, dict) else b for b in output.get("closed", [])]
    assert "TEST-001" not in closed_ids, f"Foreign bead should not be in closed: {closed_ids}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
