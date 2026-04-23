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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
