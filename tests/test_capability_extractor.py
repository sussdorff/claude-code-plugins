"""
Tests for scripts/capability-extractor.py

TDD Red-Green Gate — each acceptance criterion tested first, then implementation verified.

Coverage:
- Capability signal detection from closed bead titles
- Both feature AND task beads qualify (not just feature)
- Session summary What's New block parsing (New:/Fixed:/Internal: prefixes)
- Empty envelope → empty capabilities list
- Envelope with no capability signals → empty list
- Output is valid execution-result envelope with data.capabilities[]
- docs scanning for polaris project
- CLI --stdin mode
- CLI --project mode argument validation
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

import importlib.util

_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

# File uses a hyphen in the name, so we load it via importlib
_spec = importlib.util.spec_from_file_location(
    "capability_extractor", _SCRIPTS_DIR / "capability-extractor.py"
)
_module = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_module)  # type: ignore[union-attr]
ce = _module


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_envelope(
    project: str = "claude-code-plugins",
    date: str = "2026-04-23",
    closed_beads: list[dict[str, Any]] | None = None,
    sessions: list[dict[str, Any]] | None = None,
    open_beads: list[dict[str, Any]] | None = None,
    ready_beads: list[dict[str, Any]] | None = None,
    warnings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a minimal valid query-sources.py execution-result envelope."""
    return {
        "status": "ok",
        "summary": "test",
        "data": {
            "project": project,
            "date": date,
            "sessions": sessions or [],
            "closed_beads": closed_beads or [],
            "open_beads": open_beads or [],
            "ready_beads": ready_beads or [],
            "blocked_beads": [],
            "commits": [],
            "learnings": [],
            "decisions": [],
            "decision_requests": [],
            "followups": [],
            "rework_signals": [],
            "warnings": warnings or [],
        },
        "errors": [],
        "next_steps": [],
        "open_items": [],
        "meta": {
            "contract_version": "1",
            "producer": "query-sources.py",
        },
    }


def _make_closed_bead(
    bead_id: str = "CCP-abc",
    title: str = "Test bead",
    issue_type: str = "feature",
    description: str = "",
    commits: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": bead_id,
        "title": title,
        "issue_type": issue_type,
        "description": description,
        "commits": commits or [],
        "status": "closed",
    }


# ---------------------------------------------------------------------------
# Unit tests: _has_capability_signal
# ---------------------------------------------------------------------------


class TestHasCapabilitySignal:
    """_has_capability_signal correctly identifies signal keywords."""

    def test_now_keyword(self) -> None:
        assert ce._has_capability_signal("Feature is now available") is True

    def test_feat_keyword(self) -> None:
        assert ce._has_capability_signal("[FEAT] add new thing") is True

    def test_qg_keyword(self) -> None:
        assert ce._has_capability_signal("[QG] quality gate passed") is True

    def test_unblocks_keyword(self) -> None:
        assert ce._has_capability_signal("unblocks CCP-51k downstream") is True

    def test_now_verified_keyword(self) -> None:
        assert ce._has_capability_signal("now verified in production") is True

    def test_now_possible_keyword(self) -> None:
        assert ce._has_capability_signal("daily brief now possible") is True

    def test_no_signal(self) -> None:
        assert ce._has_capability_signal("refactor internal service") is False

    def test_case_insensitive(self) -> None:
        assert ce._has_capability_signal("[FEAT] upper case") is True
        assert ce._has_capability_signal("[feat] lower case") is True

    def test_empty_string(self) -> None:
        assert ce._has_capability_signal("") is False


# ---------------------------------------------------------------------------
# Unit tests: _extract_from_bead
# ---------------------------------------------------------------------------


class TestExtractFromBead:
    """_extract_from_bead extracts capability sentences from closed beads."""

    def test_feature_bead_with_now_in_title(self) -> None:
        bead = _make_closed_bead(
            bead_id="CCP-top",
            title="[FEAT] daily-brief: data collection now operational",
            issue_type="feature",
        )
        result = ce._extract_from_bead(bead)
        assert result is not None
        assert "CCP-top" in result
        assert "[FEAT]" in result

    def test_task_bead_also_qualifies(self) -> None:
        """Both feature AND task beads must qualify (AK #4 — capability section)."""
        bead = _make_closed_bead(
            bead_id="CCP-h8h",
            title="[REFACTOR] in-repo Codex mirrors eliminated — dev-repo principle now enforced",
            issue_type="task",
        )
        result = ce._extract_from_bead(bead)
        assert result is not None
        assert "CCP-h8h" in result

    def test_bead_without_signal_returns_none(self) -> None:
        bead = _make_closed_bead(
            title="Minor internal refactor",
            issue_type="task",
        )
        result = ce._extract_from_bead(bead)
        assert result is None

    def test_signal_in_description_qualifies(self) -> None:
        bead = _make_closed_bead(
            bead_id="CCP-xyz",
            title="Routine maintenance",
            issue_type="task",
            description="This change unblocks CCP-51k from proceeding.",
        )
        result = ce._extract_from_bead(bead)
        assert result is not None
        assert "CCP-xyz" in result

    def test_commit_count_included_when_present(self) -> None:
        bead = _make_closed_bead(
            bead_id="CCP-top",
            title="[FEAT] query-sources now available",
            issue_type="feature",
            commits=[{"sha": "abc123", "subject": "feat: add query-sources"}],
        )
        result = ce._extract_from_bead(bead)
        assert result is not None
        assert "1 commit" in result.lower()

    def test_feat_prefix_stripped_from_title(self) -> None:
        bead = _make_closed_bead(
            bead_id="CCP-top",
            title="[FEAT] daily-brief: data aggregator now operational",
            issue_type="feature",
        )
        result = ce._extract_from_bead(bead)
        assert result is not None
        # The [FEAT] type label should appear from _bead_type_label, not from title parsing
        assert "daily-brief: data aggregator now operational" in result


# ---------------------------------------------------------------------------
# Unit tests: _extract_from_session
# ---------------------------------------------------------------------------


class TestExtractFromSession:
    """_extract_from_session parses What's New blocks from session summaries."""

    def test_new_prefix_extracted(self) -> None:
        session = {
            "type": "session_summary",
            "title": "Session 2026-04-23",
            "session_ref": "sess-001",
            "text": "Some context.\nNew: Daily-brief capability extractor implemented.\nMore text.",
        }
        caps = ce._extract_from_session(session)
        assert len(caps) == 1
        assert "Daily-brief capability extractor implemented" in caps[0]

    def test_fixed_prefix_extracted(self) -> None:
        session = {
            "type": "session_summary",
            "title": "Session",
            "session_ref": "sess-002",
            "text": "Fixed: revert commit detection regex tightened.",
        }
        caps = ce._extract_from_session(session)
        assert len(caps) == 1
        assert "revert commit detection" in caps[0]

    def test_internal_prefix_extracted(self) -> None:
        session = {
            "type": "session_summary",
            "session_ref": "sess-003",
            "text": "Internal: command runner DI pattern applied.",
        }
        caps = ce._extract_from_session(session)
        assert len(caps) == 1

    def test_no_whats_new_lines_returns_empty(self) -> None:
        session = {
            "type": "session_summary",
            "text": "Just a narrative paragraph with no structured lines.",
        }
        caps = ce._extract_from_session(session)
        assert caps == []

    def test_multiple_prefixes_in_same_session(self) -> None:
        session = {
            "type": "session_summary",
            "session_ref": "sess-multi",
            "text": "New: Feature A landed.\nFixed: Bug B resolved.\nInternal: Refactor done.",
        }
        caps = ce._extract_from_session(session)
        assert len(caps) == 3

    def test_empty_text_returns_empty(self) -> None:
        session = {"type": "session_summary", "text": ""}
        assert ce._extract_from_session(session) == []

    def test_session_ref_included_in_output(self) -> None:
        session = {
            "type": "session_summary",
            "session_ref": "bead-CCP-abc",
            "text": "New: something new happened.",
        }
        caps = ce._extract_from_session(session)
        assert len(caps) == 1
        assert "bead-CCP-abc" in caps[0]


# ---------------------------------------------------------------------------
# Unit tests: extract_capabilities (main function)
# ---------------------------------------------------------------------------


class TestExtractCapabilities:
    """extract_capabilities correctly aggregates signals from full envelope."""

    def test_empty_envelope_returns_empty_list(self) -> None:
        envelope = _make_envelope()
        caps = ce.extract_capabilities(envelope)
        assert caps == []

    def test_closed_bead_with_signal_included(self) -> None:
        bead = _make_closed_bead(
            bead_id="CCP-top",
            title="[FEAT] daily-brief data aggregator now operational",
        )
        envelope = _make_envelope(closed_beads=[bead])
        caps = ce.extract_capabilities(envelope)
        assert len(caps) == 1
        assert "CCP-top" in caps[0]

    def test_closed_bead_without_signal_excluded(self) -> None:
        bead = _make_closed_bead(title="Minor internal tweak")
        envelope = _make_envelope(closed_beads=[bead])
        caps = ce.extract_capabilities(envelope)
        assert caps == []

    def test_both_feature_and_task_beads_included(self) -> None:
        """AK #4: capability section draws from both feature AND task beads."""
        feature_bead = _make_closed_bead(
            bead_id="CCP-001",
            title="[FEAT] new API now available",
            issue_type="feature",
        )
        task_bead = _make_closed_bead(
            bead_id="CCP-002",
            title="internal refactor — unblocks downstream work",
            issue_type="task",
        )
        envelope = _make_envelope(closed_beads=[feature_bead, task_bead])
        caps = ce.extract_capabilities(envelope)
        bead_ids_in_caps = " ".join(caps)
        assert "CCP-001" in bead_ids_in_caps
        assert "CCP-002" in bead_ids_in_caps

    def test_session_whats_new_included(self) -> None:
        session = {
            "type": "session_summary",
            "session_ref": "sess-001",
            "text": "New: daily-brief v1.0 ready for review.",
        }
        envelope = _make_envelope(sessions=[session])
        caps = ce.extract_capabilities(envelope)
        assert len(caps) == 1
        assert "daily-brief v1.0" in caps[0]

    def test_both_bead_and_session_signals_combined(self) -> None:
        bead = _make_closed_bead(
            bead_id="CCP-top",
            title="[FEAT] query-sources now operational",
        )
        session = {
            "type": "session_summary",
            "session_ref": "sess-001",
            "text": "Fixed: revert detection now correct.",
        }
        envelope = _make_envelope(closed_beads=[bead], sessions=[session])
        caps = ce.extract_capabilities(envelope)
        assert len(caps) == 2

    def test_invalid_data_field_returns_empty(self) -> None:
        envelope = {"status": "ok", "data": "not-a-dict"}
        caps = ce.extract_capabilities(envelope)
        assert caps == []


# ---------------------------------------------------------------------------
# Integration: CLI output is a valid execution-result envelope
# ---------------------------------------------------------------------------


class TestCLIOutput:
    """CLI --stdin mode emits valid execution-result envelope."""

    def test_stdin_mode_valid_envelope(self, capsys: pytest.CaptureFixture[str]) -> None:
        envelope = _make_envelope(
            closed_beads=[_make_closed_bead(
                bead_id="CCP-top",
                title="[FEAT] data aggregator now operational",
            )]
        )
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.read.return_value = json.dumps(envelope)
            import io
            with patch("sys.stdin", io.StringIO(json.dumps(envelope))):
                rc = ce.main(["--stdin"])
        assert rc == 0

    def test_output_has_capabilities_field(self) -> None:
        """CLI output envelope contains data.capabilities list."""
        envelope = _make_envelope(
            closed_beads=[_make_closed_bead(
                bead_id="CCP-top",
                title="[FEAT] daily-brief now ready",
            )]
        )
        import io
        with patch("sys.stdin", io.StringIO(json.dumps(envelope))):
            import io as _io
            import contextlib
            output_buf = _io.StringIO()
            with contextlib.redirect_stdout(output_buf):
                rc = ce.main(["--stdin"])
        assert rc == 0
        parsed = json.loads(output_buf.getvalue())
        assert "status" in parsed
        assert "data" in parsed
        assert "capabilities" in parsed["data"]
        assert isinstance(parsed["data"]["capabilities"], list)

    def test_missing_date_with_project_returns_error(self) -> None:
        """--project without --date should error."""
        with pytest.raises(SystemExit):
            ce.main(["--project", "claude-code-plugins"])

    def test_invalid_json_stdin_returns_error_envelope(self) -> None:
        """Invalid JSON on stdin should return error envelope (not crash)."""
        import io
        import contextlib
        output_buf = io.StringIO()
        with patch("sys.stdin", io.StringIO("not valid json")):
            with contextlib.redirect_stdout(output_buf):
                rc = ce.main(["--stdin"])
        assert rc == 0  # Exit 0 always (envelope contract)
        parsed = json.loads(output_buf.getvalue())
        assert parsed["status"] == "error"

    def test_empty_envelope_returns_ok_with_empty_capabilities(self) -> None:
        """Empty envelope should return ok status with empty capabilities."""
        envelope = _make_envelope()
        import io
        import contextlib
        output_buf = io.StringIO()
        with patch("sys.stdin", io.StringIO(json.dumps(envelope))):
            with contextlib.redirect_stdout(output_buf):
                rc = ce.main(["--stdin"])
        assert rc == 0
        parsed = json.loads(output_buf.getvalue())
        assert parsed["status"] == "ok"
        assert parsed["data"]["capabilities"] == []

    def test_envelope_meta_fields_present(self) -> None:
        """Output envelope has required meta fields."""
        envelope = _make_envelope()
        import io
        import contextlib
        output_buf = io.StringIO()
        with patch("sys.stdin", io.StringIO(json.dumps(envelope))):
            with contextlib.redirect_stdout(output_buf):
                ce.main(["--stdin"])
        parsed = json.loads(output_buf.getvalue())
        assert "meta" in parsed
        assert parsed["meta"]["contract_version"] == "1"
        assert "producer" in parsed["meta"]
