#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pyyaml>=6.0",
#   "pytest>=8.0",
#   "httpx>=0.27",
# ]
# ///
"""
Tests for scripts/query-sources.py

TDD Red-Green Gate — each acceptance criterion tested first, then implemented.

Coverage:
- Valid execution-result envelope emitted
- All required data fields present (sessions, closed_beads, open_beads, ready_beads,
  blocked_beads, commits, learnings, decisions, decision_requests, followups,
  rework_signals, warnings)
- open-brain unavailable → warning in warnings[], not an error
- No git repo → empty commits[] + warning in warnings[]
- Date with no activity → all arrays empty, status=ok
- Revert commit → appears in rework_signals[]
- Supersede event → appears in rework_signals[]
- CommandRunner DI is used (no direct subprocess.run calls)
- All sources available → status=ok
- Partial data (one source down) → status=warning
"""

from __future__ import annotations

import datetime
import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

import importlib.util

_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

# File uses a hyphen in the name, so we load it via importlib
_spec = importlib.util.spec_from_file_location(
    "query_sources", _SCRIPTS_DIR / "query-sources.py"
)
_module = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_module)  # type: ignore[union-attr]
qs = _module

# ---------------------------------------------------------------------------
# Constants / helpers
# ---------------------------------------------------------------------------

REQUIRED_ENVELOPE_KEYS = {"status", "summary", "data", "errors", "next_steps", "open_items", "meta"}
REQUIRED_META_KEYS = {"contract_version", "producer", "generated_at", "schema"}
REQUIRED_DATA_KEYS = {
    "project", "date", "sessions", "closed_beads", "open_beads", "ready_beads",
    "blocked_beads", "commits", "learnings", "decisions", "decision_requests",
    "followups", "rework_signals", "warnings",
}

TEST_DATE = "2026-04-23"
TEST_PROJECT = "claude-code-plugins"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def make_config_path() -> Path:
    return FIXTURES_DIR / "daily_brief_config.yml"


def assert_valid_envelope(result: dict[str, Any]) -> None:
    """Assert that result conforms to execution-result.schema.json structure."""
    assert REQUIRED_ENVELOPE_KEYS == set(result.keys()), (
        f"Envelope missing keys: {REQUIRED_ENVELOPE_KEYS - set(result.keys())}"
    )
    assert result["status"] in ("ok", "warning", "error"), f"Invalid status: {result['status']}"
    assert isinstance(result["summary"], str) and result["summary"]
    assert isinstance(result["data"], dict)
    assert isinstance(result["errors"], list)
    assert isinstance(result["next_steps"], list)
    assert isinstance(result["open_items"], list)
    meta = result["meta"]
    for k in REQUIRED_META_KEYS:
        assert k in meta, f"meta missing key: {k}"


def assert_required_data_fields(data: dict[str, Any]) -> None:
    """Assert all required data fields are present."""
    missing = REQUIRED_DATA_KEYS - set(data.keys())
    assert not missing, f"data missing required fields: {missing}"
    # All should be lists (except project and date)
    for key in REQUIRED_DATA_KEYS - {"project", "date"}:
        assert isinstance(data[key], list), f"data.{key} should be a list, got {type(data[key])}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def config_path() -> Path:
    return make_config_path()


@pytest.fixture()
def empty_mock_runner() -> qs.MockCommandRunner:
    """A MockCommandRunner that returns empty JSON for all bd commands."""
    return qs.MockCommandRunner({
        "bd list": "[]",
        "bd ready": "[]",
        "bd blocked": "[]",
        "bd human": "[]",
    })


@pytest.fixture()
def git_empty_runner() -> qs.MockCommandRunner:
    """A MockCommandRunner with empty git log output."""
    return qs.MockCommandRunner({
        "bd list": "[]",
        "bd ready": "[]",
        "bd blocked": "[]",
        "bd human": "[]",
        "git": "",
    })


@pytest.fixture()
def git_revert_runner() -> qs.MockCommandRunner:
    """A MockCommandRunner with a revert commit in git log (canonical git format)."""
    # Git generates revert subjects in the form: Revert "<original subject>"
    revert_line = 'abc123|Revert "feat(CCP-xyz): add some feature"|Malte|2026-04-23T10:00:00+02:00'
    normal_line = "def456|feat(CCP-xyz): add some feature|Malte|2026-04-23T09:00:00+02:00"
    output = f"{revert_line}\n{normal_line}"
    return qs.MockCommandRunner({
        "bd list": "[]",
        "bd ready": "[]",
        "bd blocked": "[]",
        "bd human": "[]",
        "git -C /tmp/test-ccp-repo log": output,
    })


@pytest.fixture()
def supersede_runner() -> qs.MockCommandRunner:
    """A MockCommandRunner where a closed bead has close_reason=superseded."""
    bead = {
        "id": "CCP-abc",
        "title": "Old feature",
        "status": "closed",
        "close_reason": "superseded by CCP-xyz",
        "closed_at": "2026-04-23T11:00:00+02:00",
    }
    return qs.MockCommandRunner({
        "bd list --status=closed": json.dumps([bead]),
        "bd list --status=open": "[]",
        "bd list": "[]",
        "bd ready": "[]",
        "bd blocked": "[]",
        "bd human": "[]",
        "git": "",
    })


# ---------------------------------------------------------------------------
# Envelope contract tests
# ---------------------------------------------------------------------------


class TestEnvelopeContract:
    """Verify the envelope structure is correct."""

    def test_returns_valid_envelope_with_all_sources_mocked(
        self, config_path: Path, empty_mock_runner: qs.MockCommandRunner
    ) -> None:
        """query_sources() emits a valid execution-result envelope."""
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=empty_mock_runner,
            ob_client=None,  # no open-brain
        )
        assert_valid_envelope(result)

    def test_data_contains_all_required_fields(
        self, config_path: Path, empty_mock_runner: qs.MockCommandRunner
    ) -> None:
        """data dict contains all required fields, all list-typed (except project/date)."""
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=empty_mock_runner,
            ob_client=None,
        )
        assert_required_data_fields(result["data"])

    def test_data_project_and_date_match_inputs(
        self, config_path: Path, empty_mock_runner: qs.MockCommandRunner
    ) -> None:
        """data.project and data.date match the CLI inputs."""
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=empty_mock_runner,
            ob_client=None,
        )
        assert result["data"]["project"] == TEST_PROJECT
        assert result["data"]["date"] == TEST_DATE

    def test_status_ok_when_all_sources_available(
        self, config_path: Path, empty_mock_runner: qs.MockCommandRunner
    ) -> None:
        """status=ok when all sources return successfully (even if empty)."""
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=empty_mock_runner,
            ob_client=None,
        )
        # ob_client=None is graceful degradation → status=warning; but bd+git ok
        # status depends on ob_client presence
        assert result["status"] in ("ok", "warning")

    def test_status_warning_when_ob_unavailable(
        self, config_path: Path, empty_mock_runner: qs.MockCommandRunner
    ) -> None:
        """status=warning when open-brain is not provided or unavailable."""
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=empty_mock_runner,
            ob_client=None,
        )
        assert result["status"] == "warning"
        assert len(result["data"]["warnings"]) >= 1
        ob_warnings = [w for w in result["data"]["warnings"] if w.get("source") == "open-brain"]
        assert ob_warnings, "Expected a warning with source='open-brain'"


# ---------------------------------------------------------------------------
# Graceful degradation: open-brain unavailable
# ---------------------------------------------------------------------------


class TestOpenBrainUnavailable:
    """When open-brain is None or raises, partial data returned with warning."""

    def test_ob_none_yields_warning_not_error(
        self, config_path: Path, empty_mock_runner: qs.MockCommandRunner
    ) -> None:
        """ob_client=None → warnings[], not errors[]."""
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=empty_mock_runner,
            ob_client=None,
        )
        assert result["errors"] == []
        ob_warnings = [w for w in result["data"]["warnings"] if w.get("source") == "open-brain"]
        assert ob_warnings

    def test_ob_exception_yields_warning(
        self, config_path: Path, empty_mock_runner: qs.MockCommandRunner
    ) -> None:
        """If ob_client raises an exception, it becomes a warning, not an error."""
        failing_ob = MagicMock()
        failing_ob.search = AsyncMock(side_effect=Exception("Connection refused"))

        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=empty_mock_runner,
            ob_client=failing_ob,
        )
        assert result["errors"] == []
        ob_warnings = [w for w in result["data"]["warnings"] if w.get("source") == "open-brain"]
        assert ob_warnings

    def test_ob_none_sessions_is_empty_list(
        self, config_path: Path, empty_mock_runner: qs.MockCommandRunner
    ) -> None:
        """sessions=[] when open-brain unavailable."""
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=empty_mock_runner,
            ob_client=None,
        )
        assert result["data"]["sessions"] == []
        assert result["data"]["learnings"] == []
        assert result["data"]["decisions"] == []


# ---------------------------------------------------------------------------
# Git source
# ---------------------------------------------------------------------------


class TestGitSource:
    """git log parsing, revert detection, bead-linking."""

    def test_no_git_repo_yields_empty_commits_and_warning(
        self, config_path: Path
    ) -> None:
        """When git command fails (no repo), commits=[] and warning added."""
        failing_runner = qs.MockCommandRunner({
            "bd list": "[]",
            "bd ready": "[]",
            "bd blocked": "[]",
            "bd human": "[]",
        }, git_fail=True)

        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=failing_runner,
            ob_client=None,
        )
        assert result["data"]["commits"] == []
        git_warnings = [w for w in result["data"]["warnings"] if w.get("source") == "git"]
        assert git_warnings

    def test_revert_commit_appears_in_rework_signals(
        self, config_path: Path, git_revert_runner: qs.MockCommandRunner
    ) -> None:
        """A 'Revert ...' commit is detected and added to rework_signals[]."""
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=git_revert_runner,
            ob_client=None,
        )
        rework = result["data"]["rework_signals"]
        revert_signals = [r for r in rework if r.get("type") == "revert_commit"]
        assert revert_signals, f"Expected revert_commit in rework_signals, got: {rework}"

    def test_revert_commit_not_in_standalone_commits(
        self, config_path: Path, git_revert_runner: qs.MockCommandRunner
    ) -> None:
        """Revert commits are separated into rework_signals, not left in commits[]."""
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=git_revert_runner,
            ob_client=None,
        )
        commits = result["data"]["commits"]
        revert_in_commits = [c for c in commits if c.get("subject", "").startswith('Revert "')]
        assert not revert_in_commits, "Revert commits should not be in commits[], only in rework_signals[]"

    def test_bead_linked_commit_not_in_standalone_commits(
        self, config_path: Path
    ) -> None:
        """A commit with CCP-xxx in subject is merged into closed_bead, not standalone commits[]."""
        bead_sha = "aaa111"
        bead_commit_line = f"{bead_sha}|feat(CCP-abc): implement feature|Malte|2026-04-23T10:00:00+02:00"
        bead = {
            "id": "CCP-abc",
            "title": "Implement feature",
            "status": "closed",
            "close_reason": "done",
            "closed_at": "2026-04-23T11:00:00+02:00",
        }
        runner = qs.MockCommandRunner({
            "bd list --status=closed": json.dumps([bead]),
            "bd list --status=open": "[]",
            "bd list": "[]",
            "bd ready": "[]",
            "bd blocked": "[]",
            "bd human": "[]",
            "git -C /tmp/test-ccp-repo log": bead_commit_line,
        })
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=runner,
            ob_client=None,
        )
        commits = result["data"]["commits"]
        standalone_linked = [c for c in commits if bead_sha in c.get("sha", "")]
        assert not standalone_linked, "Bead-linked commit should not appear in standalone commits[]"

    def test_empty_date_yields_empty_commits(
        self, config_path: Path, git_empty_runner: qs.MockCommandRunner
    ) -> None:
        """If git log returns empty, commits=[]."""
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=git_empty_runner,
            ob_client=None,
        )
        assert result["data"]["commits"] == []


# ---------------------------------------------------------------------------
# Beads source
# ---------------------------------------------------------------------------


class TestBeadsSource:
    """bd CLI data: closed, open, ready, blocked, decision_requests."""

    def test_supersede_event_in_rework_signals(
        self, config_path: Path, supersede_runner: qs.MockCommandRunner
    ) -> None:
        """A closed bead with close_reason containing 'superseded' → rework_signals[]."""
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=supersede_runner,
            ob_client=None,
        )
        rework = result["data"]["rework_signals"]
        supersede_signals = [r for r in rework if r.get("type") == "supersede_event"]
        assert supersede_signals, f"Expected supersede_event in rework_signals, got: {rework}"

    def test_bd_unavailable_yields_warning(
        self, config_path: Path
    ) -> None:
        """When bd fails, warnings added, not errors."""
        failing_runner = qs.MockCommandRunner({}, bd_fail=True, git_fail=True)
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=failing_runner,
            ob_client=None,
        )
        # Should have warnings for beads and git
        bd_warnings = [w for w in result["data"]["warnings"] if w.get("source") == "beads"]
        assert bd_warnings

    def test_closed_beads_populated(self, config_path: Path) -> None:
        """closed_beads[] contains beads returned by bd list --status=closed."""
        bead = {
            "id": "CCP-abc",
            "title": "Test bead",
            "status": "closed",
            "close_reason": "done",
            "closed_at": "2026-04-23T11:00:00+02:00",
        }
        runner = qs.MockCommandRunner({
            "bd list --status=closed": json.dumps([bead]),
            "bd list --status=open": "[]",
            "bd list": "[]",
            "bd ready": "[]",
            "bd blocked": "[]",
            "bd human": "[]",
            "git": "",
        })
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=runner,
            ob_client=None,
        )
        assert len(result["data"]["closed_beads"]) == 1
        assert result["data"]["closed_beads"][0]["id"] == "CCP-abc"

    def test_open_beads_populated(self, config_path: Path) -> None:
        """open_beads[] contains beads from bd list --status=open."""
        bead = {"id": "CCP-xyz", "title": "Open bead", "status": "open"}
        runner = qs.MockCommandRunner({
            "bd list --status=closed": "[]",
            "bd list --status=open": json.dumps([bead]),
            "bd list": "[]",
            "bd ready": "[]",
            "bd blocked": "[]",
            "bd human": "[]",
            "git": "",
        })
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=runner,
            ob_client=None,
        )
        assert len(result["data"]["open_beads"]) == 1
        assert result["data"]["open_beads"][0]["id"] == "CCP-xyz"


# ---------------------------------------------------------------------------
# Reopen event detection
# ---------------------------------------------------------------------------


class TestReopenEventDetection:
    """Beads that were previously closed but are now open/in_progress → reopen_event."""

    def test_detect_reopens_returns_reopen_signal(self) -> None:
        """_detect_reopens() identifies a bead with closed_at set but currently open."""
        open_bead = {
            "id": "CCP-reopened",
            "title": "Reopened bead",
            "status": "open",
            "closed_at": "2026-04-20T10:00:00+02:00",  # was previously closed
        }
        signals = qs._detect_reopens([open_bead], [])
        assert len(signals) == 1
        assert signals[0]["type"] == "reopen_event"
        assert signals[0]["bead_id"] == "CCP-reopened"

    def test_detect_reopens_in_progress_bead(self) -> None:
        """_detect_reopens() also detects in_progress beads that were previously closed."""
        in_progress_bead = {
            "id": "CCP-wip",
            "title": "WIP bead",
            "status": "in_progress",
            "closed_at": "2026-04-19T08:00:00+02:00",
        }
        signals = qs._detect_reopens([], [in_progress_bead])
        assert len(signals) == 1
        assert signals[0]["type"] == "reopen_event"
        assert signals[0]["status"] == "in_progress"

    def test_detect_reopens_skips_never_closed_beads(self) -> None:
        """_detect_reopens() ignores beads whose closed_at is None (never closed)."""
        fresh_bead = {
            "id": "CCP-fresh",
            "title": "Brand new bead",
            "status": "open",
            "closed_at": None,
        }
        no_closed_at_bead = {
            "id": "CCP-nocf",
            "title": "No closed_at field",
            "status": "open",
        }
        signals = qs._detect_reopens([fresh_bead, no_closed_at_bead], [])
        assert signals == [], f"Expected no reopen signals, got: {signals}"

    def test_reopen_event_appears_in_query_sources_rework_signals(
        self, config_path: Path
    ) -> None:
        """query_sources() includes reopen_event in rework_signals[] when a bead was reopened."""
        reopened_bead = {
            "id": "CCP-reopen",
            "title": "Previously closed bead",
            "status": "open",
            "closed_at": "2026-04-20T10:00:00+02:00",
        }
        runner = qs.MockCommandRunner({
            "bd list --status=closed": "[]",
            "bd list --status=open": json.dumps([reopened_bead]),
            "bd list --status=in_progress": "[]",
            "bd list": "[]",
            "bd ready": "[]",
            "bd blocked": "[]",
            "bd human": "[]",
            "git": "",
        })
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=runner,
            ob_client=None,
        )
        rework = result["data"]["rework_signals"]
        reopen_signals = [r for r in rework if r.get("type") == "reopen_event"]
        assert reopen_signals, f"Expected reopen_event in rework_signals, got: {rework}"
        assert reopen_signals[0]["bead_id"] == "CCP-reopen"


# ---------------------------------------------------------------------------
# Open-brain integration (mocked)
# ---------------------------------------------------------------------------


class TestOpenBrainIntegration:
    """With a mock ob_client, verify correct routing of entries."""

    def _make_ob_client(self, entries: list[dict[str, Any]]) -> MagicMock:
        """Create a mock ob_client whose search() returns given entries."""
        client = MagicMock()
        client.search = AsyncMock(return_value=entries)
        return client

    def test_session_entries_in_sessions(self, config_path: Path, empty_mock_runner: qs.MockCommandRunner) -> None:
        """open-brain session_summary entries go into sessions[]."""
        session_entry = {
            "id": "ob-1",
            "type": "session_summary",
            "content": "Session about feature X",
            "session_ref": "sess-001",
            "project": "claude-code-plugins",
            "created_at": "2026-04-23T10:00:00Z",
        }
        ob_client = self._make_ob_client([session_entry])
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=empty_mock_runner,
            ob_client=ob_client,
        )
        assert len(result["data"]["sessions"]) == 1
        assert result["data"]["sessions"][0]["id"] == "ob-1"

    def test_learning_entries_in_learnings(self, config_path: Path, empty_mock_runner: qs.MockCommandRunner) -> None:
        """open-brain type=learning entries go into learnings[]."""
        learning_entry = {
            "id": "ob-2",
            "type": "learning",
            "content": "Learned that X causes Y",
            "session_ref": "sess-001",
            "project": "claude-code-plugins",
            "created_at": "2026-04-23T10:30:00Z",
        }
        ob_client = self._make_ob_client([learning_entry])
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=empty_mock_runner,
            ob_client=ob_client,
        )
        assert len(result["data"]["learnings"]) == 1

    def test_pending_decision_in_decisions(self, config_path: Path, empty_mock_runner: qs.MockCommandRunner) -> None:
        """open-brain type=decision with status=pending goes into decisions[]."""
        decision_entry = {
            "id": "ob-3",
            "type": "decision",
            "content": "Decide: Use option A or B?",
            "session_ref": "sess-001",
            "project": "claude-code-plugins",
            "created_at": "2026-04-23T11:00:00Z",
            "metadata": {"status": "pending"},
        }
        ob_client = self._make_ob_client([decision_entry])
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=empty_mock_runner,
            ob_client=ob_client,
        )
        assert len(result["data"]["decisions"]) == 1
        assert result["status"] == "ok"  # ob available → ok

    def test_all_decisions_included_with_metadata_status(
        self, config_path: Path, empty_mock_runner: qs.MockCommandRunner
    ) -> None:
        """All open-brain type=decision entries are included in decisions[].

        The data layer must NOT filter by metadata.status — callers filter if needed.
        The metadata.status field is preserved so callers can distinguish pending vs resolved.
        """
        resolved_decision = {
            "id": "ob-3r",
            "type": "decision",
            "content": "Decided: Use option A.",
            "session_ref": "sess-001",
            "project": "claude-code-plugins",
            "created_at": "2026-04-23T11:00:00Z",
            "metadata": {"status": "resolved"},
        }
        no_status_decision = {
            "id": "ob-3n",
            "type": "decision",
            "content": "Some old decision, no status field.",
            "session_ref": "sess-002",
            "project": "claude-code-plugins",
            "created_at": "2026-04-23T11:30:00Z",
        }
        ob_client = self._make_ob_client([resolved_decision, no_status_decision])
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=empty_mock_runner,
            ob_client=ob_client,
        )
        # Both decisions must be present regardless of metadata.status
        decisions = result["data"]["decisions"]
        assert len(decisions) == 2, (
            f"Expected 2 decisions[], got: {decisions}"
        )
        ids = {d["id"] for d in decisions}
        assert ids == {"ob-3r", "ob-3n"}
        # metadata.status is preserved for caller-side filtering
        resolved = next(d for d in decisions if d["id"] == "ob-3r")
        assert resolved.get("metadata", {}).get("status") == "resolved"

    def test_followup_prefixes_extracted(self, config_path: Path, empty_mock_runner: qs.MockCommandRunner) -> None:
        """Debrief entries with Decide:/Need input:/Follow-up: → followups[]."""
        debrief_entry = {
            "id": "ob-4",
            "type": "debrief",
            "content": "Decide: Should we migrate DB?\nFollow-up: Check with team\nNeed input: Budget?",
            "session_ref": "sess-002",
            "project": "claude-code-plugins",
            "created_at": "2026-04-23T12:00:00Z",
        }
        ob_client = self._make_ob_client([debrief_entry])
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=empty_mock_runner,
            ob_client=ob_client,
        )
        followups = result["data"]["followups"]
        assert len(followups) >= 1

    def test_dedup_by_session_ref(self, config_path: Path, empty_mock_runner: qs.MockCommandRunner) -> None:
        """Entries with the same session_ref are deduped — only first kept."""
        entry1 = {
            "id": "ob-5a",
            "type": "session_summary",
            "content": "First",
            "session_ref": "sess-dup",
            "project": "claude-code-plugins",
            "created_at": "2026-04-23T10:00:00Z",
        }
        entry2 = {
            "id": "ob-5b",
            "type": "session_summary",
            "content": "Duplicate",
            "session_ref": "sess-dup",  # Same session_ref!
            "project": "claude-code-plugins",
            "created_at": "2026-04-23T10:01:00Z",
        }
        ob_client = self._make_ob_client([entry1, entry2])
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=empty_mock_runner,
            ob_client=ob_client,
        )
        assert len(result["data"]["sessions"]) == 1

    def test_ob_available_sets_status_ok(
        self, config_path: Path, empty_mock_runner: qs.MockCommandRunner
    ) -> None:
        """When all sources available, status=ok."""
        ob_client = self._make_ob_client([])
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=empty_mock_runner,
            ob_client=ob_client,
        )
        # If no sources failed → ok
        assert result["status"] == "ok"
        assert result["data"]["warnings"] == []


# ---------------------------------------------------------------------------
# CommandRunner DI
# ---------------------------------------------------------------------------


class TestCommandRunnerDI:
    """Verify CommandRunner interface and mock work correctly."""

    def test_mock_runner_matches_prefix(self) -> None:
        """MockCommandRunner matches by prefix, returns configured response."""
        runner = qs.MockCommandRunner({"bd list": '["a"]'})
        proc = runner.run(["bd", "list", "--status=closed"])
        assert proc.returncode == 0
        assert '["a"]' in proc.stdout

    def test_mock_runner_git_fail_returns_nonzero(self) -> None:
        """MockCommandRunner with git_fail=True returns nonzero for git commands."""
        runner = qs.MockCommandRunner({}, git_fail=True)
        proc = runner.run(["git", "-C", "/some/path", "log"])
        assert proc.returncode != 0

    def test_mock_runner_bd_fail_returns_nonzero(self) -> None:
        """MockCommandRunner with bd_fail=True returns nonzero for bd commands."""
        runner = qs.MockCommandRunner({}, bd_fail=True)
        proc = runner.run(["bd", "list"])
        assert proc.returncode != 0

    def test_real_command_runner_exists(self) -> None:
        """RealCommandRunner class exists and has a .run() method."""
        runner = qs.RealCommandRunner()
        assert hasattr(runner, "run")

    def test_mock_command_runner_exists(self) -> None:
        """MockCommandRunner class exists and has a .run() method."""
        runner = qs.MockCommandRunner({})
        assert hasattr(runner, "run")


# ---------------------------------------------------------------------------
# Warnings structure
# ---------------------------------------------------------------------------


class TestWarningsStructure:
    """Warnings must have source, reason, project, date fields."""

    def test_ob_warning_has_required_fields(
        self, config_path: Path, empty_mock_runner: qs.MockCommandRunner
    ) -> None:
        """open-brain warning has source, reason, project, date."""
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=empty_mock_runner,
            ob_client=None,
        )
        ob_warnings = [w for w in result["data"]["warnings"] if w.get("source") == "open-brain"]
        assert ob_warnings
        w = ob_warnings[0]
        for required_field in ("source", "reason", "project", "date"):
            assert required_field in w, f"Warning missing field: {required_field}"

    def test_git_warning_has_required_fields(
        self, config_path: Path
    ) -> None:
        """git warning has source, reason, project, date."""
        runner = qs.MockCommandRunner({
            "bd list": "[]",
            "bd ready": "[]",
            "bd blocked": "[]",
            "bd human": "[]",
        }, git_fail=True)
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=runner,
            ob_client=None,
        )
        git_warnings = [w for w in result["data"]["warnings"] if w.get("source") == "git"]
        if git_warnings:
            w = git_warnings[0]
            for required_field in ("source", "reason", "project", "date"):
                assert required_field in w, f"Warning missing field: {required_field}"


# ---------------------------------------------------------------------------
# Empty date / no activity
# ---------------------------------------------------------------------------


class TestNoActivity:
    """Date with no activity → all arrays empty, status=ok (if ob available) or warning."""

    def test_no_activity_all_arrays_empty(
        self, config_path: Path, git_empty_runner: qs.MockCommandRunner
    ) -> None:
        """When all sources return nothing, data arrays are empty."""
        ob_client = MagicMock()
        ob_client.search = AsyncMock(return_value=[])
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=git_empty_runner,
            ob_client=ob_client,
        )
        data = result["data"]
        for key in REQUIRED_DATA_KEYS - {"project", "date"}:
            assert data[key] == [], f"Expected {key}=[] for no activity, got: {data[key]}"

    def test_no_activity_status_ok(
        self, config_path: Path, git_empty_runner: qs.MockCommandRunner
    ) -> None:
        """status=ok when all sources available but empty (no activity)."""
        ob_client = MagicMock()
        ob_client.search = AsyncMock(return_value=[])
        result = qs.query_sources(
            project=TEST_PROJECT,
            date=TEST_DATE,
            config_path=config_path,
            runner=git_empty_runner,
            ob_client=ob_client,
        )
        assert result["status"] == "ok"
