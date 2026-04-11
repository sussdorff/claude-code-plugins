"""Tests for council.py — input parsing, cross-bead table, scenario detection."""

from __future__ import annotations

import json
import pytest

from malte.skills.council.council import (
    classify_severity,
    consolidate_findings,
    consolidate_findings_cross_bead,
    detect_missing_scenario,
    has_critical_findings,
    parse_council_input,
)


# ---------------------------------------------------------------------------
# Helpers: fake bd_runner for parse_council_input
# ---------------------------------------------------------------------------

def _make_bd_runner(success: bool = True, has_children: bool = False):
    """Return a callable that fakes `bd show <id> --json`."""
    def runner(bead_id: str) -> dict:
        if not success:
            raise RuntimeError(f"bd show {bead_id} failed")
        result = {"id": bead_id, "title": f"Bead {bead_id}", "type": "feature"}
        if has_children:
            result["children"] = [
                {"id": "child-1", "title": "Child 1"},
                {"id": "child-2", "title": "Child 2"},
            ]
        else:
            result["children"] = []
        return result
    return runner


# ===========================================================================
# AK1: bead without prefix -> epic mode (if children) or bead mode (if not)
# ===========================================================================

class TestParseCouncilInputBeadAndEpic:
    def test_bead_mode_no_children(self):
        """A bare ID with no children -> bead mode."""
        result = parse_council_input("5shz", bd_runner=_make_bd_runner(success=True, has_children=False))
        assert result["mode"] == "bead"
        assert result["value"] == "5shz"

    def test_epic_mode_with_children(self):
        """A bare ID with children -> epic mode."""
        result = parse_council_input("5shz", bd_runner=_make_bd_runner(success=True, has_children=True))
        assert result["mode"] == "epic"
        assert result["value"] == "5shz"

    def test_bead_data_returned(self):
        """The bead_data from bd show should be included in result."""
        result = parse_council_input("abc1", bd_runner=_make_bd_runner(success=True, has_children=False))
        assert "bead_data" in result
        assert result["bead_data"]["id"] == "abc1"


# ===========================================================================
# AK2: .md or / -> file mode (existing logic, unchanged)
# ===========================================================================

class TestParseCouncilInputFile:
    def test_md_extension(self):
        result = parse_council_input("docs/spec.md")
        assert result["mode"] == "file"
        assert result["value"] == "docs/spec.md"

    def test_path_with_slash(self):
        result = parse_council_input("malte/skills/council/SKILL.md")
        assert result["mode"] == "file"
        assert result["value"] == "malte/skills/council/SKILL.md"

    def test_path_with_slash_no_md(self):
        result = parse_council_input("src/main.py")
        assert result["mode"] == "file"
        assert result["value"] == "src/main.py"

    def test_id_containing_md_not_file_mode(self):
        """A bead ID like 'cmd5' should NOT match file mode (no .md suffix)."""
        result = parse_council_input("cmd5", bd_runner=_make_bd_runner(success=True, has_children=False))
        assert result["mode"] == "bead"
        assert result["value"] == "cmd5"

    def test_existing_file_without_md_or_slash(self, tmp_path):
        """A bare filename that exists on disk should be detected as file mode."""
        testfile = tmp_path / "Makefile"
        testfile.write_text("all: build")
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = parse_council_input("Makefile")
            assert result["mode"] == "file"
            assert result["value"] == "Makefile"
        finally:
            os.chdir(old_cwd)


# ===========================================================================
# AK3: label:<name> -> label mode
# ===========================================================================

class TestParseCouncilInputLabel:
    def test_label_prefix(self):
        result = parse_council_input("label:security")
        assert result["mode"] == "label"
        assert result["value"] == "security"

    def test_label_prefix_complex(self):
        result = parse_council_input("label:phase-2")
        assert result["mode"] == "label"
        assert result["value"] == "phase-2"


# ===========================================================================
# AK4: unknown arg -> clear error
# ===========================================================================

class TestParseCouncilInputUnknown:
    def test_unknown_arg_raises(self):
        with pytest.raises(ValueError, match="Not a file, not a known bead ID"):
            parse_council_input("xyzzy999", bd_runner=_make_bd_runner(success=False))

    def test_error_message_mentions_label(self):
        with pytest.raises(ValueError, match=r"label:<name>"):
            parse_council_input("nope", bd_runner=_make_bd_runner(success=False))

    def test_json_decode_error_becomes_valueerror(self):
        """bd_runner raising RuntimeError from malformed JSON -> ValueError."""
        def bad_json_runner(bead_id: str) -> dict:
            raise RuntimeError(f"bd show {bead_id} returned invalid JSON: not-json")
        with pytest.raises(ValueError, match="Not a file, not a known bead ID"):
            parse_council_input("badid", bd_runner=bad_json_runner)


# ===========================================================================
# AK5: detect_missing_scenario
# ===========================================================================

class TestDetectMissingScenario:
    def test_no_scenario_section(self):
        desc = "# Feature\n\nSome description\n\n## Acceptance Criteria\n- AK1\n"
        assert detect_missing_scenario(desc) is True

    def test_has_szenario_section(self):
        desc = "# Feature\n\n## Szenario\n\nAs a user...\n"
        assert detect_missing_scenario(desc) is False

    def test_has_scenario_section_english(self):
        desc = "# Feature\n\n## Scenario\n\nGiven something...\n"
        assert detect_missing_scenario(desc) is False

    def test_empty_string(self):
        assert detect_missing_scenario("") is True

    def test_scenario_in_body_not_heading(self):
        desc = "# Feature\n\nThis scenario is great\n"
        assert detect_missing_scenario(desc) is True

    def test_scenario_heading_with_trailing_content(self):
        """## Szenario (Draft) should still be detected as a scenario heading."""
        desc = "# Feature\n\n## Szenario (Draft)\n\nAs a user...\n"
        assert detect_missing_scenario(desc) is False


# ===========================================================================
# AK6: cross-bead table has Bead column
# ===========================================================================

class TestConsolidateFindingsCrossBead:
    def test_bead_column_in_header(self):
        findings_by_bead = {
            "bead-1": [
                "COUNCIL-REVIEW: End-User\n\n- [WARNING] UX: Bad flow → Fix it"
            ],
            "bead-2": [
                "COUNCIL-REVIEW: Developer\n\n- [CRITICAL] API: Missing auth → Add auth"
            ],
        }
        table = consolidate_findings_cross_bead(findings_by_bead)
        assert "| # | Bead | Severity | Agent | Thema | Finding | Empfehlung |" in table

    def test_bead_id_in_rows(self):
        findings_by_bead = {
            "bead-1": [
                "COUNCIL-REVIEW: End-User\n\n- [WARNING] UX: Bad flow → Fix it"
            ],
        }
        table = consolidate_findings_cross_bead(findings_by_bead)
        assert "bead-1" in table

    def test_empty_findings_returns_no_findings(self):
        """When no findings are parsed, return 'No findings.' instead of header-only table."""
        findings_by_bead = {
            "bead-1": ["COUNCIL-REVIEW: End-User\n\nAll looks good, no issues."],
        }
        result = consolidate_findings_cross_bead(findings_by_bead)
        assert result == "No findings."

    def test_sorted_by_severity(self):
        findings_by_bead = {
            "bead-1": [
                "COUNCIL-REVIEW: Dev\n\n- [NOTE] Style: Minor → Ignore",
                "COUNCIL-REVIEW: Sec\n\n- [CRITICAL] Auth: Missing → Add",
            ],
        }
        table = consolidate_findings_cross_bead(findings_by_bead)
        lines = table.strip().split("\n")
        # First data row (after header + separator) should be CRITICAL
        data_rows = [l for l in lines if l.startswith("| ") and not l.startswith("| #") and not l.startswith("|--")]
        assert "CRITICAL" in data_rows[0]
        assert "NOTE" in data_rows[1]


# ===========================================================================
# AK8: existing consolidate_findings still produces single-bead format (regression)
# ===========================================================================

class TestConsolidateFindingsRegression:
    def test_single_bead_no_bead_column(self):
        outputs = [
            "COUNCIL-REVIEW: End-User\n\n- [WARNING] UX: Bad flow → Fix it"
        ]
        table = consolidate_findings(outputs)
        assert "| # | Severity | Agent |" in table
        # Must NOT have Bead column
        assert "| # | Bead |" not in table
