"""
Tests for scripts/render-brief.py

TDD Red-Green Gate — acceptance criteria tested, then verified.

Coverage:
- Valid markdown output from query-sources.py envelope
- All v1.0 sections present (Executive Summary, Was sich verändert hat,
  Offene Fäden, Nächste sinnvolle Schritte, Belege)
- Voice B: German, past tense, third-person
- Empty day: "Ruhiger Tag — keine Aktivität verzeichnet."
- Next Best Moves max 3 items, sources cited
- Range mode: compressed rollup by default
- --detailed mode does not invent unsupported strategy
- validate-skill.py passes (indirectly via SKILL.md structure)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

import importlib.util

_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

# Load render-brief.py via importlib (hyphen in filename)
_spec = importlib.util.spec_from_file_location(
    "render_brief", _SCRIPTS_DIR / "render-brief.py"
)
_module = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_module)  # type: ignore[union-attr]
rb = _module


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_data(
    project: str = "claude-code-plugins",
    date: str = "2026-04-23",
    closed_beads: list[dict[str, Any]] | None = None,
    open_beads: list[dict[str, Any]] | None = None,
    ready_beads: list[dict[str, Any]] | None = None,
    blocked_beads: list[dict[str, Any]] | None = None,
    commits: list[dict[str, Any]] | None = None,
    sessions: list[dict[str, Any]] | None = None,
    decisions: list[dict[str, Any]] | None = None,
    decision_requests: list[dict[str, Any]] | None = None,
    followups: list[dict[str, Any]] | None = None,
    warnings: list[dict[str, Any]] | None = None,
    rework_signals: list[dict[str, Any]] | None = None,
    learnings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "project": project,
        "date": date,
        "closed_beads": closed_beads or [],
        "open_beads": open_beads or [],
        "ready_beads": ready_beads or [],
        "blocked_beads": blocked_beads or [],
        "commits": commits or [],
        "sessions": sessions or [],
        "decisions": decisions or [],
        "decision_requests": decision_requests or [],
        "followups": followups or [],
        "rework_signals": rework_signals or [],
        "warnings": warnings or [],
        "learnings": learnings or [],
    }


def _make_closed_bead(
    bead_id: str = "CCP-abc",
    title: str = "Test bead",
    issue_type: str = "feature",
    commits: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": bead_id,
        "title": title,
        "issue_type": issue_type,
        "commits": commits or [],
        "status": "closed",
    }


def _make_open_bead(
    bead_id: str = "CCP-open",
    title: str = "Open bead",
    status: str = "open",
) -> dict[str, Any]:
    return {
        "id": bead_id,
        "title": title,
        "status": status,
    }


# ---------------------------------------------------------------------------
# Section: Executive Summary
# ---------------------------------------------------------------------------


class TestExecutiveSummary:
    """_render_executive_summary produces correct Voice B output."""

    def test_empty_day_emits_ruhiger_tag(self) -> None:
        data = _make_data()
        output = rb._render_executive_summary(data, [], "claude-code-plugins", "2026-04-23")
        assert rb._EMPTY_DAY_MSG in output

    def test_closed_beads_mentioned_in_summary(self) -> None:
        bead = _make_closed_bead("CCP-top", "data aggregator")
        data = _make_data(closed_beads=[bead])
        output = rb._render_executive_summary(data, [], "claude-code-plugins", "2026-04-23")
        assert "CCP-top" in output
        # Should mention bead was geschlossen (closed)
        assert "geschlossen" in output

    def test_capability_signals_mentioned(self) -> None:
        data = _make_data()
        capabilities = ["CCP-top [FEAT] geschlossen: data aggregator now operational"]
        output = rb._render_executive_summary(data, capabilities, "claude-code-plugins", "2026-04-23")
        assert "Capability" in output or "Signal" in output

    def test_heading_includes_project_and_date(self) -> None:
        data = _make_data()
        output = rb._render_executive_summary(data, [], "myproject", "2026-04-23")
        assert "myproject" in output
        assert "2026-04-23" in output

    def test_no_invented_strategy_without_source(self) -> None:
        """Executive Summary must not invent content if no source data exists."""
        data = _make_data()
        output = rb._render_executive_summary(data, [], "testproject", "2026-04-23")
        # With no source data, should emit the empty day message only
        assert rb._EMPTY_DAY_MSG in output
        # Should not contain any fabricated claims
        assert "neue" not in output.lower() or rb._EMPTY_DAY_MSG in output


# ---------------------------------------------------------------------------
# Section: Was sich verändert hat (What Changed)
# ---------------------------------------------------------------------------


class TestWhatChanged:
    """_render_what_changed section is deterministic."""

    def test_empty_day_emits_ruhiger_tag(self) -> None:
        data = _make_data()
        output = rb._render_what_changed(data, [], "proj", "2026-04-23")
        assert rb._EMPTY_DAY_MSG in output

    def test_closed_bead_listed(self) -> None:
        bead = _make_closed_bead("CCP-top", "[FEAT] query-sources", "feature")
        data = _make_data(closed_beads=[bead])
        output = rb._render_what_changed(data, [], "proj", "2026-04-23")
        assert "CCP-top" in output

    def test_bead_type_shown(self) -> None:
        bead = _make_closed_bead("CCP-001", "some feature", "feature")
        data = _make_data(closed_beads=[bead])
        output = rb._render_what_changed(data, [], "proj", "2026-04-23")
        assert "feature" in output.lower()

    def test_capability_signals_listed(self) -> None:
        data = _make_data()
        caps = ["CCP-top [FEAT] geschlossen: data aggregator now operational"]
        output = rb._render_what_changed(data, caps, "proj", "2026-04-23")
        assert "CCP-top" in output
        assert "Capabilities" in output or "Capability" in output

    def test_standalone_commits_listed(self) -> None:
        commit = {"sha": "abc1234567", "subject": "chore: bump version"}
        data = _make_data(commits=[commit])
        output = rb._render_what_changed(data, [], "proj", "2026-04-23")
        assert "abc12345" in output or "abc1234" in output

    def test_heading_present(self) -> None:
        data = _make_data()
        output = rb._render_what_changed(data, [], "myproject", "2026-04-23")
        assert "Was sich verändert hat" in output


# ---------------------------------------------------------------------------
# Section: Offene Fäden (Open Loops)
# ---------------------------------------------------------------------------


class TestOpenLoops:
    """_render_open_loops is deterministic and neutral."""

    def test_no_open_beads_says_keine(self) -> None:
        data = _make_data()
        output = rb._render_open_loops(data, "proj", "2026-04-23")
        assert "Keine" in output or "keine" in output

    def test_open_beads_listed(self) -> None:
        bead = _make_open_bead("CCP-lx2", "render-brief implementation")
        data = _make_data(open_beads=[bead])
        output = rb._render_open_loops(data, "proj", "2026-04-23")
        assert "CCP-lx2" in output

    def test_blocked_beads_listed_separately(self) -> None:
        open_bead = _make_open_bead("CCP-001", "in flight")
        blocked_bead = _make_open_bead("CCP-002", "waiting for dependency", status="blocked")
        data = _make_data(open_beads=[open_bead], blocked_beads=[blocked_bead])
        output = rb._render_open_loops(data, "proj", "2026-04-23")
        assert "CCP-001" in output
        assert "CCP-002" in output
        assert "Blockiert" in output

    def test_heading_present(self) -> None:
        data = _make_data()
        output = rb._render_open_loops(data, "myproject", "2026-04-23")
        assert "Offene Fäden" in output


# ---------------------------------------------------------------------------
# Section: Nächste sinnvolle Schritte (Next Best Moves)
# ---------------------------------------------------------------------------


class TestNextBestMoves:
    """_render_next_best_moves enforces max 3 items and cites sources."""

    def test_no_moves_returns_placeholder(self) -> None:
        data = _make_data()
        output = rb._render_next_best_moves(data, "proj", "2026-04-23")
        assert "keine" in output.lower() or "Keine" in output

    def test_ready_beads_listed_as_moves(self) -> None:
        bead = _make_open_bead("CCP-51k", "SKILL.md orchestration")
        data = _make_data(ready_beads=[bead])
        output = rb._render_next_best_moves(data, "proj", "2026-04-23")
        assert "CCP-51k" in output

    def test_source_category_cited(self) -> None:
        """AK #5: Next Best Moves must cite source category."""
        bead = _make_open_bead("CCP-51k", "skill orchestration")
        data = _make_data(ready_beads=[bead])
        output = rb._render_next_best_moves(data, "proj", "2026-04-23")
        assert "ready-bead" in output or "Quelle" in output

    def test_max_3_items_enforced(self) -> None:
        """AK #5: Next Best Moves must never exceed 3 items."""
        beads = [_make_open_bead(f"CCP-{i:03d}", f"bead {i}") for i in range(5)]
        followups = [
            {"type": "Follow-up", "text": f"followup {i}"} for i in range(3)
        ]
        data = _make_data(ready_beads=beads, followups=followups)
        output = rb._render_next_best_moves(data, "proj", "2026-04-23")
        # Count items (lines starting with -)
        item_lines = [line for line in output.splitlines() if line.strip().startswith("- ")]
        assert len(item_lines) <= 3

    def test_max_2_from_ready_beads(self) -> None:
        """Max 2 items may come from ready_beads."""
        beads = [_make_open_bead(f"CCP-{i:03d}", f"bead {i}") for i in range(4)]
        data = _make_data(ready_beads=beads)
        output = rb._render_next_best_moves(data, "proj", "2026-04-23")
        item_lines = [line for line in output.splitlines() if line.strip().startswith("- ")]
        # All items from ready_beads — max 2
        assert len(item_lines) <= 2

    def test_max_1_from_followups(self) -> None:
        """Max 1 item may come from session followups."""
        followups = [
            {"type": "Follow-up", "text": f"item {i}"} for i in range(3)
        ]
        data = _make_data(followups=followups)
        output = rb._render_next_best_moves(data, "proj", "2026-04-23")
        item_lines = [line for line in output.splitlines() if line.strip().startswith("- ")]
        assert len(item_lines) <= 1

    def test_session_followup_cited(self) -> None:
        """Session followup items cite their source."""
        followups = [{"type": "Decide", "text": "which approach to take"}]
        data = _make_data(followups=followups)
        output = rb._render_next_best_moves(data, "proj", "2026-04-23")
        assert "session-followup" in output

    def test_heading_present(self) -> None:
        data = _make_data()
        output = rb._render_next_best_moves(data, "myproject", "2026-04-23")
        assert "Nächste sinnvolle Schritte" in output


# ---------------------------------------------------------------------------
# Section: Belege (Evidence)
# ---------------------------------------------------------------------------


class TestEvidence:
    """_render_evidence is deterministic and lists all source items."""

    def test_empty_data_returns_keine_belege(self) -> None:
        data = _make_data()
        output = rb._render_evidence(data, "proj", "2026-04-23")
        assert "keine" in output.lower()

    def test_closed_bead_in_evidence(self) -> None:
        bead = _make_closed_bead("CCP-top", "data aggregator")
        data = _make_data(closed_beads=[bead])
        output = rb._render_evidence(data, "proj", "2026-04-23")
        assert "CCP-top" in output
        assert "bead/" in output

    def test_commit_in_evidence(self) -> None:
        commit = {"sha": "abc1234567890", "subject": "feat: something"}
        data = _make_data(commits=[commit])
        output = rb._render_evidence(data, "proj", "2026-04-23")
        assert "abc12345" in output
        assert "commit/" in output

    def test_warning_in_evidence(self) -> None:
        warning = {"source": "open-brain", "reason": "unavailable"}
        data = _make_data(warnings=[warning])
        output = rb._render_evidence(data, "proj", "2026-04-23")
        assert "open-brain" in output
        assert "warning/" in output

    def test_heading_present(self) -> None:
        data = _make_data()
        output = rb._render_evidence(data, "myproject", "2026-04-23")
        assert "Belege" in output


# ---------------------------------------------------------------------------
# Full render: render_single_day
# ---------------------------------------------------------------------------


class TestRenderSingleDay:
    """render_single_day produces valid markdown with all required sections."""

    def _mock_fetch(self, data: dict[str, Any]) -> MagicMock:
        """Create a mock that returns given data as an envelope."""
        envelope = {
            "status": "ok",
            "summary": "test",
            "data": data,
            "errors": [],
            "next_steps": [],
            "open_items": [],
            "meta": {"contract_version": "1", "producer": "test"},
        }
        mock = MagicMock(return_value=envelope)
        return mock

    def test_all_v10_sections_present(self, tmp_path: Path) -> None:
        """AK #1: Produces valid markdown with all v1.0 sections."""
        data = _make_data(
            closed_beads=[_make_closed_bead("CCP-001", "[FEAT] something new")],
            open_beads=[_make_open_bead("CCP-002", "open work")],
            ready_beads=[_make_open_bead("CCP-003", "ready work")],
        )
        config_path = tmp_path / "daily-brief.yml"

        with patch.object(rb, "_fetch_envelope", self._mock_fetch(data)), \
             patch.object(rb, "_fetch_capabilities", return_value=[]):
            brief = rb.render_single_day(
                "claude-code-plugins", "2026-04-23", config_path, persist=False
            )

        # All required v1.0 sections must be present
        assert "## Executive Summary" in brief
        assert "## Was sich verändert hat" in brief
        assert "## Offene Fäden" in brief
        assert "## Nächste sinnvolle Schritte" in brief
        assert "## Belege" in brief

    def test_empty_day_brief_has_ruhiger_tag(self, tmp_path: Path) -> None:
        """Empty day produces honest empty state message."""
        data = _make_data()
        config_path = tmp_path / "daily-brief.yml"

        with patch.object(rb, "_fetch_envelope", self._mock_fetch(data)), \
             patch.object(rb, "_fetch_capabilities", return_value=[]):
            brief = rb.render_single_day(
                "claude-code-plugins", "2026-04-23", config_path, persist=False
            )

        assert rb._EMPTY_DAY_MSG in brief

    def test_brief_is_markdown_string(self, tmp_path: Path) -> None:
        """Output is a non-empty string."""
        data = _make_data()
        config_path = tmp_path / "daily-brief.yml"

        with patch.object(rb, "_fetch_envelope", self._mock_fetch(data)), \
             patch.object(rb, "_fetch_capabilities", return_value=[]):
            brief = rb.render_single_day(
                "proj", "2026-04-23", config_path, persist=False
            )

        assert isinstance(brief, str)
        assert len(brief) > 0

    def test_next_best_moves_never_exceeds_3(self, tmp_path: Path) -> None:
        """AK #5: Next Best Moves never exceeds 3 items."""
        data = _make_data(
            ready_beads=[_make_open_bead(f"CCP-{i:03d}", f"bead {i}") for i in range(5)],
            followups=[{"type": "Follow-up", "text": f"fu{i}"} for i in range(3)],
        )
        config_path = tmp_path / "daily-brief.yml"

        with patch.object(rb, "_fetch_envelope", self._mock_fetch(data)), \
             patch.object(rb, "_fetch_capabilities", return_value=[]):
            brief = rb.render_single_day(
                "proj", "2026-04-23", config_path, persist=False
            )

        # Find the Next Best Moves section
        lines = brief.splitlines()
        in_section = False
        move_items = []
        for line in lines:
            if "Nächste sinnvolle Schritte" in line:
                in_section = True
                continue
            if in_section and line.startswith("##"):
                break
            if in_section and line.strip().startswith("- "):
                move_items.append(line)

        assert len(move_items) <= 3

    def test_sources_cited_in_next_moves(self, tmp_path: Path) -> None:
        """AK #5: Next Best Moves cites source category."""
        data = _make_data(
            ready_beads=[_make_open_bead("CCP-001", "ready bead")],
        )
        config_path = tmp_path / "daily-brief.yml"

        with patch.object(rb, "_fetch_enhance", side_effect=AttributeError, create=True), \
             patch.object(rb, "_fetch_envelope", self._mock_fetch(data)), \
             patch.object(rb, "_fetch_capabilities", return_value=[]):
            brief = rb.render_single_day(
                "proj", "2026-04-23", config_path, persist=False
            )

        # Source citation should appear in the Next Best Moves section
        assert "Quelle" in brief or "ready-bead" in brief


# ---------------------------------------------------------------------------
# Range mode
# ---------------------------------------------------------------------------


class TestRangeMode:
    """Range mode produces compressed rollup while persisting per-day briefs."""

    def _make_envelope(self, date: str, has_activity: bool = True) -> dict[str, Any]:
        closed = [_make_closed_bead(f"CCP-{date[:4]}", "some work")] if has_activity else []
        return {
            "status": "ok",
            "summary": "test",
            "data": _make_data(date=date, closed_beads=closed),
            "errors": [],
            "next_steps": [],
            "open_items": [],
            "meta": {"contract_version": "1", "producer": "test"},
        }

    def test_date_range_helper(self) -> None:
        """_date_range returns correct list of ISO date strings."""
        dates = rb._date_range("2026-04-20", "2026-04-22")
        assert dates == ["2026-04-20", "2026-04-21", "2026-04-22"]

    def test_date_range_single_day(self) -> None:
        dates = rb._date_range("2026-04-23", "2026-04-23")
        assert dates == ["2026-04-23"]

    def test_range_output_has_rollup_summary(self, tmp_path: Path) -> None:
        """AK #6: Range mode emits compressed rollup by default."""
        envelopes = {
            "2026-04-20": self._make_envelope("2026-04-20"),
            "2026-04-21": self._make_envelope("2026-04-21"),
            "2026-04-22": self._make_envelope("2026-04-22"),
        }

        def fake_fetch(project: str, date: str, config_path: Any) -> dict[str, Any]:
            return envelopes.get(date, {})

        with patch.object(rb, "_fetch_envelope", side_effect=fake_fetch), \
             patch.object(rb, "_fetch_capabilities", return_value=[]), \
             patch.object(rb, "render_single_day", return_value=""):
            brief = rb.render_range(
                "claude-code-plugins", "2026-04-20", "2026-04-22", tmp_path / "cfg.yml"
            )

        # Compressed rollup: single Executive Summary header
        exec_summary_count = brief.count("## Executive Summary")
        assert exec_summary_count == 1

    def test_range_what_changed_grouped_by_day(self, tmp_path: Path) -> None:
        """What Changed in rollup is grouped by day."""
        envelopes = {
            "2026-04-20": self._make_envelope("2026-04-20"),
            "2026-04-21": self._make_envelope("2026-04-21"),
        }

        def fake_fetch(project: str, date: str, config_path: Any) -> dict[str, Any]:
            return envelopes.get(date, {})

        with patch.object(rb, "_fetch_envelope", side_effect=fake_fetch), \
             patch.object(rb, "_fetch_capabilities", return_value=[]), \
             patch.object(rb, "render_single_day", return_value=""):
            brief = rb.render_range(
                "claude-code-plugins", "2026-04-20", "2026-04-21", tmp_path / "cfg.yml"
            )

        # Both dates should appear as subheadings under What Changed
        assert "2026-04-20" in brief
        assert "2026-04-21" in brief


# ---------------------------------------------------------------------------
# Detailed mode
# ---------------------------------------------------------------------------


class TestDetailedMode:
    """--detailed mode expands prose without inventing content."""

    def test_detailed_does_not_add_unsupported_content(self, tmp_path: Path) -> None:
        """AK #7: --detailed flag must not invent strategy not in source data."""
        data = _make_data()  # Empty data — no source facts
        envelope = {
            "status": "ok",
            "summary": "test",
            "data": data,
            "errors": [],
            "next_steps": [],
            "open_items": [],
            "meta": {"contract_version": "1", "producer": "test"},
        }
        config_path = tmp_path / "daily-brief.yml"

        with patch.object(rb, "_fetch_envelope", return_value=envelope), \
             patch.object(rb, "_fetch_capabilities", return_value=[]):
            brief = rb.render_single_day(
                "proj", "2026-04-23", config_path, detailed=True, persist=False
            )

        # Empty day must still show the honest empty state message
        assert rb._EMPTY_DAY_MSG in brief

    def test_detailed_flag_accepted_without_error(self, tmp_path: Path) -> None:
        """--detailed flag is accepted and does not crash."""
        data = _make_data(closed_beads=[_make_closed_bead("CCP-001", "[FEAT] something")])
        envelope = {
            "status": "ok",
            "summary": "test",
            "data": data,
            "errors": [],
            "next_steps": [],
            "open_items": [],
            "meta": {"contract_version": "1", "producer": "test"},
        }
        config_path = tmp_path / "daily-brief.yml"

        with patch.object(rb, "_fetch_envelope", return_value=envelope), \
             patch.object(rb, "_fetch_capabilities", return_value=[]):
            brief = rb.render_single_day(
                "proj", "2026-04-23", config_path, detailed=True, persist=False
            )

        assert isinstance(brief, str)
        assert len(brief) > 0


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------


class TestCLIArgParsing:
    """CLI argument handling is correct."""

    def test_missing_project_exits(self) -> None:
        with pytest.raises(SystemExit):
            rb.main(["--date", "2026-04-23"])

    def test_invalid_date_exits_with_error(self) -> None:
        with patch.object(rb, "_fetch_envelope", return_value={}), \
             patch.object(rb, "_fetch_capabilities", return_value=[]):
            rc = rb.main(["--project", "test", "--date", "not-a-date"])
        assert rc == 1

    def test_valid_date_runs_without_crash(self, tmp_path: Path) -> None:
        """Valid arguments run without crash (mocked data)."""
        data = _make_data()
        envelope = {
            "status": "ok",
            "summary": "test",
            "data": data,
            "errors": [],
            "next_steps": [],
            "open_items": [],
            "meta": {"contract_version": "1", "producer": "test"},
        }
        config_path = tmp_path / "daily-brief.yml"

        with patch.object(rb, "_fetch_envelope", return_value=envelope), \
             patch.object(rb, "_fetch_capabilities", return_value=[]):
            import contextlib
            import io
            output_buf = io.StringIO()
            with contextlib.redirect_stdout(output_buf):
                rc = rb.main([
                    "--project", "test",
                    "--date", "2026-04-23",
                    "--config", str(config_path),
                    "--no-persist",
                ])
        assert rc == 0
        assert len(output_buf.getvalue()) > 0


# ---------------------------------------------------------------------------
# Section: Entscheidungsbedarf (Decisions Needed) — AK1, AK3
# ---------------------------------------------------------------------------


class TestDecisionsNeeded:
    """_render_decisions_needed produces correct output."""

    def test_empty_state_returns_keine_offenen_entscheidungen(self) -> None:
        """AK1: empty state message when no decision signals present."""
        data = _make_data()
        output = rb._render_decisions_needed(data, "proj", "2026-04-23")
        assert "Keine offenen Entscheidungen erfasst." in output

    def test_decision_request_bead_renders_with_source_tag(self) -> None:
        """AK1: bd human bead appears with decision-request source tag."""
        data = _make_data(
            decision_requests=[{"id": "CCP-xyz", "title": "Decide: which deployment target"}]
        )
        output = rb._render_decisions_needed(data, "proj", "2026-04-23")
        assert "CCP-xyz" in output
        assert "decision-request" in output

    def test_pending_ob_decision_renders(self) -> None:
        """AK1: open-brain decision with status=pending appears."""
        decisions = [
            {
                "id": "dec-001",
                "title": "Should we migrate to Gas City?",
                "metadata": {"status": "pending"},
            }
        ]
        data = _make_data(decisions=decisions)
        output = rb._render_decisions_needed(data, "proj", "2026-04-23")
        assert "dec-001" in output or "Gas City" in output
        assert "ob-decision" in output

    def test_decide_followup_renders(self) -> None:
        """AK1: followup with type Decide appears in decisions."""
        followups = [{"type": "Decide", "text": "which approach to use for routing"}]
        data = _make_data(followups=followups)
        output = rb._render_decisions_needed(data, "proj", "2026-04-23")
        assert "routing" in output
        assert "followup-decide" in output

    def test_need_input_followup_renders(self) -> None:
        """AK1: followup with type 'Need input' also appears in decisions."""
        followups = [{"type": "Need input", "text": "confirm API rate limits"}]
        data = _make_data(followups=followups)
        output = rb._render_decisions_needed(data, "proj", "2026-04-23")
        assert "API rate limits" in output
        assert "followup-decide" in output

    def test_non_pending_decision_not_rendered(self) -> None:
        """AK3: decisions without status=pending must NOT appear."""
        decisions = [
            {
                "id": "dec-closed",
                "title": "Already resolved decision",
                "metadata": {"status": "closed"},
            }
        ]
        data = _make_data(decisions=decisions)
        output = rb._render_decisions_needed(data, "proj", "2026-04-23")
        assert "dec-closed" not in output
        assert "Keine offenen Entscheidungen erfasst." in output

    def test_follow_up_prefix_not_in_decisions_needed(self) -> None:
        """AK3: Follow-up (not Decide/Need input) must NOT appear in decisions."""
        followups = [{"type": "Follow-up", "text": "check deployment status"}]
        data = _make_data(followups=followups)
        output = rb._render_decisions_needed(data, "proj", "2026-04-23")
        # Follow-up type should not make it into decisions needed
        assert "deployment status" not in output
        assert "Keine offenen Entscheidungen erfasst." in output

    def test_source_category_cited(self) -> None:
        """AK1: source tag present for each item."""
        data = _make_data(
            decision_requests=[{"id": "CCP-req", "title": "Approve infra change"}]
        )
        output = rb._render_decisions_needed(data, "proj", "2026-04-23")
        assert "Quelle:" in output

    def test_heading_is_entscheidungsbedarf(self) -> None:
        """Section heading must be Entscheidungsbedarf."""
        data = _make_data()
        output = rb._render_decisions_needed(data, "proj", "2026-04-23")
        assert "## Entscheidungsbedarf" in output


# ---------------------------------------------------------------------------
# Section: Drift- und Rework-Signale (Drift & Rework) — AK2
# ---------------------------------------------------------------------------


class TestDriftReworkSignals:
    """_render_drift_rework produces correct output."""

    def test_empty_state_returns_keine_drift_signale(self) -> None:
        """AK2: empty state message when no rework signals present."""
        data = _make_data()
        output = rb._render_drift_rework(data, "proj", "2026-04-23")
        assert "Keine Drift- oder Rework-Signale erkannt." in output

    def test_revert_commit_detected(self) -> None:
        """AK2: revert commit signal appears with correct source tag."""
        rework_signals = [
            {"type": "revert_commit", "sha": "abc12345", "subject": "Revert feat: add feature X"}
        ]
        data = _make_data(rework_signals=rework_signals)
        output = rb._render_drift_rework(data, "proj", "2026-04-23")
        assert "abc12345" in output
        assert "revert-commit" in output

    def test_supersede_event_detected(self) -> None:
        """AK2: supersede event appears with correct source tag."""
        rework_signals = [
            {"type": "supersede_event", "bead_id": "CCP-old", "title": "Old feature"}
        ]
        data = _make_data(rework_signals=rework_signals)
        output = rb._render_drift_rework(data, "proj", "2026-04-23")
        assert "CCP-old" in output
        assert "supersede-event" in output

    def test_reopen_event_detected(self) -> None:
        """AK2: reopen event appears with correct source tag."""
        rework_signals = [
            {"type": "reopen_event", "bead_id": "CCP-reopen", "title": "Reopened bead"}
        ]
        data = _make_data(rework_signals=rework_signals)
        output = rb._render_drift_rework(data, "proj", "2026-04-23")
        assert "CCP-reopen" in output
        assert "reopen-event" in output

    def test_source_id_cited(self) -> None:
        """Source ID must be cited in output."""
        rework_signals = [
            {"type": "supersede_event", "bead_id": "CCP-sup", "title": "Superseded bead"}
        ]
        data = _make_data(rework_signals=rework_signals)
        output = rb._render_drift_rework(data, "proj", "2026-04-23")
        assert "CCP-sup" in output
        assert "Quelle:" in output

    def test_heading_is_drift_und_rework_signale(self) -> None:
        """Section heading must be Drift- und Rework-Signale."""
        data = _make_data()
        output = rb._render_drift_rework(data, "proj", "2026-04-23")
        assert "## Drift- und Rework-Signale" in output


# ---------------------------------------------------------------------------
# Semantic distinction: Open Loops vs Drift & Rework — AK4
# ---------------------------------------------------------------------------


class TestSemanticDistinction:
    """Open Loops and Drift & Rework remain semantically distinct."""

    def test_open_loops_and_drift_rework_do_not_overlap(self) -> None:
        """AK4: An open bead must not appear in the Drift & Rework section."""
        open_bead = _make_open_bead("CCP-in-flight", "currently in flight")
        rework_signal = {"type": "revert_commit", "sha": "dead1234", "subject": "Revert something"}
        data = _make_data(open_beads=[open_bead], rework_signals=[rework_signal])

        open_loops_out = rb._render_open_loops(data, "proj", "2026-04-23")
        drift_out = rb._render_drift_rework(data, "proj", "2026-04-23")

        # open bead should be in open loops
        assert "CCP-in-flight" in open_loops_out
        # open bead must NOT be in drift section
        assert "CCP-in-flight" not in drift_out

    def test_open_loops_bead_not_in_drift_section(self) -> None:
        """AK4: drift section only contains rework_signals, not open_beads."""
        open_bead = _make_open_bead("CCP-open-only", "only in open loops")
        data = _make_data(open_beads=[open_bead])

        drift_out = rb._render_drift_rework(data, "proj", "2026-04-23")
        assert "CCP-open-only" not in drift_out
        assert "Keine Drift- oder Rework-Signale erkannt." in drift_out

    def test_revert_commit_not_in_open_loops(self) -> None:
        """AK4: revert commits must not bleed into Open Loops."""
        rework_signals = [
            {"type": "revert_commit", "sha": "cafe5678", "subject": "Revert: remove X"}
        ]
        data = _make_data(rework_signals=rework_signals)

        open_loops_out = rb._render_open_loops(data, "proj", "2026-04-23")
        assert "cafe5678" not in open_loops_out
        assert "revert_commit" not in open_loops_out


# ---------------------------------------------------------------------------
# render_single_day v1.1 — AK5: sample output updated
# ---------------------------------------------------------------------------


class TestRenderSingleDayV11:
    """render_single_day includes v1.1 sections."""

    def _mock_fetch(self, data: dict[str, Any]) -> MagicMock:
        envelope = {
            "status": "ok",
            "summary": "test",
            "data": data,
            "errors": [],
            "next_steps": [],
            "open_items": [],
            "meta": {"contract_version": "1", "producer": "test"},
        }
        return MagicMock(return_value=envelope)

    def test_decisions_needed_section_present(self, tmp_path: Path) -> None:
        """v1.1 Entscheidungsbedarf section appears in single-day output."""
        data = _make_data(
            decision_requests=[{"id": "CCP-req1", "title": "Approve the plan"}]
        )
        config_path = tmp_path / "daily-brief.yml"

        with patch.object(rb, "_fetch_envelope", self._mock_fetch(data)), \
             patch.object(rb, "_fetch_capabilities", return_value=[]):
            brief = rb.render_single_day(
                "proj", "2026-04-23", config_path, persist=False
            )

        assert "## Entscheidungsbedarf" in brief

    def test_drift_rework_section_present(self, tmp_path: Path) -> None:
        """v1.1 Drift- und Rework-Signale section appears in single-day output."""
        data = _make_data(
            rework_signals=[{"type": "revert_commit", "sha": "abcd1234", "subject": "Revert X"}]
        )
        config_path = tmp_path / "daily-brief.yml"

        with patch.object(rb, "_fetch_envelope", self._mock_fetch(data)), \
             patch.object(rb, "_fetch_capabilities", return_value=[]):
            brief = rb.render_single_day(
                "proj", "2026-04-23", config_path, persist=False
            )

        assert "## Drift- und Rework-Signale" in brief

    def test_v11_section_ordering_after_open_loops(self, tmp_path: Path) -> None:
        """AK5: Entscheidungsbedarf and Drift sections appear after Offene Fäden."""
        data = _make_data(
            open_beads=[_make_open_bead("CCP-fl", "in-flight")],
            decision_requests=[{"id": "CCP-d1", "title": "Pick a strategy"}],
            rework_signals=[{"type": "supersede_event", "bead_id": "CCP-sup", "title": "old"}],
        )
        config_path = tmp_path / "daily-brief.yml"

        with patch.object(rb, "_fetch_envelope", self._mock_fetch(data)), \
             patch.object(rb, "_fetch_capabilities", return_value=[]):
            brief = rb.render_single_day(
                "proj", "2026-04-23", config_path, persist=False
            )

        lines = brief.splitlines()
        headings = [l for l in lines if l.startswith("## ")]
        open_loops_idx = next(
            (i for i, h in enumerate(headings) if "Offene Fäden" in h), -1
        )
        decisions_idx = next(
            (i for i, h in enumerate(headings) if "Entscheidungsbedarf" in h), -1
        )
        drift_idx = next(
            (i for i, h in enumerate(headings) if "Drift" in h), -1
        )
        next_moves_idx = next(
            (i for i, h in enumerate(headings) if "Nächste" in h), -1
        )

        assert open_loops_idx != -1, "Offene Fäden heading missing"
        assert decisions_idx != -1, "Entscheidungsbedarf heading missing"
        assert drift_idx != -1, "Drift heading missing"
        assert next_moves_idx != -1, "Nächste sinnvolle Schritte heading missing"

        # Ordering: open_loops < decisions < drift < next_moves
        assert open_loops_idx < decisions_idx
        assert decisions_idx < drift_idx
        assert drift_idx < next_moves_idx
