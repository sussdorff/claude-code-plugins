"""Tests for CCP-o4z: SessionEnd safety-net Stop hook.

Verifies all acceptance criteria:
  AK1: Stop hook registered in hooks.json under the Stop event type
  AK2: Hook exits 0 (non-blocking) when stop_hook_active is true (loop prevention)
  AK3: Hook is a no-op when cwd is not inside a Claude Code worktree
  AK4: Hook extracts bead_id from worktree path (pattern: bead-<id> in path)
  AK5: Hook appends a safety-net note when bead is still in_progress
  AK6: Hook is a no-op (dedup) when bead status is closed
  AK7: Always exits 0, never exits 2, informational stdout on action
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).parent.parent
HOOKS_JSON = REPO_ROOT / "beads-workflow" / "hooks" / "hooks.json"
SESSION_END_PY = REPO_ROOT / "beads-workflow" / "hooks" / "session-end.py"


def _load_session_end():
    """Load session-end.py as a module (filename contains hyphen, can't use plain import)."""
    spec = importlib.util.spec_from_file_location("session_end", SESSION_END_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# AK1: hooks.json registration
# ---------------------------------------------------------------------------

class TestHooksJsonRegistration:
    """AK1 — Stop hook is registered in hooks.json."""

    def test_hooks_json_has_stop_key(self):
        """AK1: hooks.json must contain a 'Stop' event key."""
        data = json.loads(HOOKS_JSON.read_text())
        assert "Stop" in data.get("hooks", {}), (
            "hooks.json must register a 'Stop' event handler"
        )

    def test_stop_hook_has_session_end_command(self):
        """AK1: The Stop handler must reference session-end.py."""
        data = json.loads(HOOKS_JSON.read_text())
        stop_entries = data.get("hooks", {}).get("Stop", [])
        found = False
        for entry in stop_entries:
            for hook in entry.get("hooks", []):
                if "session-end.py" in hook.get("command", ""):
                    found = True
                    break
        assert found, (
            "hooks.json Stop section must include a command referencing session-end.py"
        )

    def test_stop_hook_type_is_command(self):
        """AK1: The Stop hook entry must use type='command'."""
        data = json.loads(HOOKS_JSON.read_text())
        stop_entries = data.get("hooks", {}).get("Stop", [])
        for entry in stop_entries:
            for hook in entry.get("hooks", []):
                if "session-end.py" in hook.get("command", ""):
                    assert hook.get("type") == "command", (
                        "session-end.py hook must have type='command'"
                    )
                    return
        pytest.fail("session-end.py hook not found in Stop entries")

    def test_stop_hook_has_timeout(self):
        """AK1: The Stop hook entry must define a timeout."""
        data = json.loads(HOOKS_JSON.read_text())
        stop_entries = data.get("hooks", {}).get("Stop", [])
        for entry in stop_entries:
            for hook in entry.get("hooks", []):
                if "session-end.py" in hook.get("command", ""):
                    assert "timeout" in hook, (
                        "session-end.py hook must define a timeout"
                    )
                    return
        pytest.fail("session-end.py hook not found in Stop entries")


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

def _make_payload(cwd: str, stop_hook_active: bool = False) -> dict:
    """Build a minimal Stop hook stdin payload."""
    return {
        "stop_hook_active": stop_hook_active,
        "cwd": cwd,
    }


# ---------------------------------------------------------------------------
# AK2: Loop prevention — stop_hook_active
# ---------------------------------------------------------------------------

class TestLoopPrevention:
    """AK2 — Hook is a no-op when stop_hook_active is True."""

    def test_noop_when_stop_hook_active(self):
        """AK2: When stop_hook_active=True, handle() returns without calling bd."""
        session_end = _load_session_end()

        payload = _make_payload(
            cwd="/Users/malte/.claude/worktrees/bead-CCP-abc",
            stop_hook_active=True,
        )
        with patch("subprocess.run") as mock_run:
            session_end.handle(payload)
            mock_run.assert_not_called()

    def test_loop_prevention_produces_no_output(self, capsys):
        """AK2: Loop-prevention path should not print anything."""
        session_end = _load_session_end()

        payload = _make_payload(
            cwd="/Users/malte/.claude/worktrees/bead-CCP-abc",
            stop_hook_active=True,
        )
        with patch("subprocess.run"):
            session_end.handle(payload)
        out = capsys.readouterr().out
        assert out == "", "Loop-prevention path must produce no output"


# ---------------------------------------------------------------------------
# AK3: No-op outside of worktree
# ---------------------------------------------------------------------------

class TestWorktreeGuard:
    """AK3 — Hook is a no-op when cwd is not inside a Claude Code worktree."""

    def test_noop_when_not_in_worktree(self):
        """AK3: cwd without .claude/worktrees/ in path → no bd call."""
        session_end = _load_session_end()

        payload = _make_payload(cwd="/Users/malte/code/some-other-project")
        with patch("subprocess.run") as mock_run:
            session_end.handle(payload)
            mock_run.assert_not_called()

    def test_noop_for_home_directory(self):
        """AK3: home directory cwd → no bd call."""
        session_end = _load_session_end()

        payload = _make_payload(cwd="/Users/malte")
        with patch("subprocess.run") as mock_run:
            session_end.handle(payload)
            mock_run.assert_not_called()

    def test_active_in_worktree(self):
        """AK3: cwd with .claude/worktrees/ in path → bd show IS called."""
        session_end = _load_session_end()

        payload = _make_payload(cwd="/Users/malte/.claude/worktrees/bead-CCP-abc")
        bead_json = json.dumps({"id": "CCP-abc", "status": "in_progress"})

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=bead_json, stderr=""
            )
            session_end.handle(payload)
            # At minimum bd show must have been called
            assert mock_run.call_count >= 1, (
                "handle() must call subprocess.run at least once for worktree paths"
            )


# ---------------------------------------------------------------------------
# AK4: Bead ID extraction
# ---------------------------------------------------------------------------

class TestBeadIdExtraction:
    """AK4 — Bead ID is extracted correctly from the worktree path."""

    def test_extract_bead_id_simple(self):
        """AK4: extract_bead_id returns correct id from standard worktree path."""
        session_end = _load_session_end()

        bead_id = session_end.extract_bead_id(
            "/Users/malte/.claude/worktrees/bead-CCP-o4z"
        )
        assert bead_id == "CCP-o4z"

    def test_extract_bead_id_with_suffix(self):
        """AK4: extract_bead_id works when cwd is a subdirectory of the worktree."""
        session_end = _load_session_end()

        bead_id = session_end.extract_bead_id(
            "/Users/malte/.claude/worktrees/bead-CCP-xyz/subdir/nested"
        )
        assert bead_id == "CCP-xyz"

    def test_extract_bead_id_returns_none_for_non_worktree(self):
        """AK4: extract_bead_id returns None for paths not matching the pattern."""
        session_end = _load_session_end()

        assert session_end.extract_bead_id("/Users/malte/code/some-project") is None

    def test_extract_bead_id_returns_none_for_missing_bead_prefix(self):
        """AK4: extract_bead_id returns None when no bead- segment in worktree path."""
        session_end = _load_session_end()

        assert session_end.extract_bead_id(
            "/Users/malte/.claude/worktrees/not-a-bead"
        ) is None

    def test_extract_bead_id_dotted_suffix(self):
        """AK4: extract_bead_id handles dotted IDs like CCP-2vo.8."""
        session_end = _load_session_end()

        bead_id = session_end.extract_bead_id(
            "/Users/malte/.claude/worktrees/bead-CCP-2vo.8"
        )
        assert bead_id == "CCP-2vo.8"

    def test_extract_bead_id_dotted_suffix_with_subdir(self):
        """AK4: extract_bead_id handles dotted IDs with subdirectory."""
        session_end = _load_session_end()

        bead_id = session_end.extract_bead_id(
            "/Users/malte/.claude/worktrees/bead-CCP-2hd.1/subdir"
        )
        assert bead_id == "CCP-2hd.1"


# ---------------------------------------------------------------------------
# AK5: Safety-net note for in_progress bead
# ---------------------------------------------------------------------------

class TestSafetyNetNote:
    """AK5 — Safety-net note appended when bead is in_progress."""

    def test_appends_note_for_in_progress_bead(self, capsys):
        """AK5: bd update --append-notes is called when bead status is in_progress."""
        session_end = _load_session_end()

        payload = _make_payload(cwd="/Users/malte/.claude/worktrees/bead-CCP-abc")
        bead_json = json.dumps({"id": "CCP-abc", "status": "in_progress"})

        update_calls = []

        def fake_run(cmd, **kwargs):
            if "show" in cmd:
                return MagicMock(returncode=0, stdout=bead_json, stderr="")
            update_calls.append(cmd)
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            session_end.handle(payload)

        assert any("update" in str(c) for c in update_calls), (
            "bd update must be called for an in_progress bead"
        )
        # The note must mention session-close
        update_cmd = next(c for c in update_calls if "update" in str(c))
        assert any("session-close" in str(arg) for arg in update_cmd), (
            "The appended note must mention session-close"
        )

    def test_appends_note_when_bd_show_returns_list(self, capsys):
        """AK5: bd show --json may return a list; first element status is used."""
        session_end = _load_session_end()

        payload = _make_payload(cwd="/Users/malte/.claude/worktrees/bead-CCP-abc")
        # bd show --json returns a LIST of objects in this repo
        bead_json = json.dumps([{"id": "CCP-abc", "status": "in_progress"}])

        update_calls = []

        def fake_run(cmd, **kwargs):
            if "show" in cmd:
                return MagicMock(returncode=0, stdout=bead_json, stderr="")
            update_calls.append(cmd)
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            session_end.handle(payload)

        assert any("update" in str(c) for c in update_calls), (
            "bd update must be called when bd show returns a list with in_progress status"
        )

    def test_safety_net_prints_to_stderr(self, capsys):
        """AK7: When safety-net fires, informational text is printed to stderr (observability-only hook)."""
        session_end = _load_session_end()

        payload = _make_payload(cwd="/Users/malte/.claude/worktrees/bead-CCP-abc")
        bead_json = json.dumps({"id": "CCP-abc", "status": "in_progress"})

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=bead_json, stderr=""
            )
            session_end.handle(payload)

        captured = capsys.readouterr()
        assert not captured.out.strip(), (
            "Safety-net message must NOT go to stdout for an observability-only hook"
        )
        assert captured.err.strip(), (
            "When the safety-net note is appended, stderr must contain informational text"
        )


# ---------------------------------------------------------------------------
# AK6: Dedup protection — closed bead
# ---------------------------------------------------------------------------

class TestDedupProtection:
    """AK6 — Hook is a no-op when bead status is closed."""

    def test_noop_for_closed_bead(self):
        """AK6: No bd update call when bead status is closed."""
        session_end = _load_session_end()

        payload = _make_payload(cwd="/Users/malte/.claude/worktrees/bead-CCP-abc")
        bead_json = json.dumps({"id": "CCP-abc", "status": "closed"})

        update_calls = []

        def fake_run(cmd, **kwargs):
            if "show" in cmd:
                return MagicMock(returncode=0, stdout=bead_json, stderr="")
            update_calls.append(cmd)
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            session_end.handle(payload)

        assert not update_calls, (
            "bd update must NOT be called when bead is already closed"
        )

    def test_closed_bead_produces_no_output(self, capsys):
        """AK6: Closed bead produces no stdout output (silent dedup)."""
        session_end = _load_session_end()

        payload = _make_payload(cwd="/Users/malte/.claude/worktrees/bead-CCP-abc")
        bead_json = json.dumps({"id": "CCP-abc", "status": "closed"})

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=bead_json, stderr=""
            )
            session_end.handle(payload)

        out = capsys.readouterr().out
        assert out == "", "Closed bead must produce no output"


# ---------------------------------------------------------------------------
# AK7: Exit code standard — always 0
# ---------------------------------------------------------------------------

class TestExitCodeStandard:
    """AK7 — Hook always exits 0, never 2."""

    def test_main_exits_0_for_stop_hook_active(self, monkeypatch):
        """AK7: main() exits 0 even in loop-prevention path."""
        session_end = _load_session_end()

        payload = _make_payload(
            cwd="/Users/malte/.claude/worktrees/bead-CCP-abc",
            stop_hook_active=True,
        )
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps(payload)))
        with pytest.raises(SystemExit) as exc_info:
            session_end.main()
        assert exc_info.value.code == 0

    def test_main_exits_0_for_non_worktree(self, monkeypatch):
        """AK7: main() exits 0 for non-worktree cwd."""
        session_end = _load_session_end()

        payload = _make_payload(cwd="/Users/malte/code/some-project")
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps(payload)))
        with pytest.raises(SystemExit) as exc_info:
            session_end.main()
        assert exc_info.value.code == 0

    def test_main_exits_0_for_in_progress_bead(self, monkeypatch):
        """AK7: main() exits 0 after appending safety-net note."""
        session_end = _load_session_end()

        payload = _make_payload(cwd="/Users/malte/.claude/worktrees/bead-CCP-abc")
        bead_json = json.dumps({"id": "CCP-abc", "status": "in_progress"})

        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps(payload)))
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=bead_json, stderr=""
            )
            with pytest.raises(SystemExit) as exc_info:
                session_end.main()
        assert exc_info.value.code == 0

    def test_main_exits_0_on_bd_failure(self, monkeypatch):
        """AK7: main() exits 0 even if bd show fails."""
        session_end = _load_session_end()

        payload = _make_payload(cwd="/Users/malte/.claude/worktrees/bead-CCP-abc")
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps(payload)))
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            with pytest.raises(SystemExit) as exc_info:
                session_end.main()
        assert exc_info.value.code == 0

    def test_main_exits_0_on_invalid_json_stdin(self, monkeypatch):
        """AK7: main() exits 0 even on invalid JSON stdin."""
        session_end = _load_session_end()

        monkeypatch.setattr("sys.stdin", __import__("io").StringIO("not-json"))
        with pytest.raises(SystemExit) as exc_info:
            session_end.main()
        assert exc_info.value.code == 0
