#!/usr/bin/env python3
"""
Unit tests for vision-author skill components:
  - scripts/vision_renderer.py  (VisionAnswers -> vision.md text)
  - scripts/vision_conformance.py  (v1 conformance scanner for --refresh)
  - tense-gate integration (rendered output passes tense gate)
  - refresh mode conformance checks

RED phase: all tests import from modules that don't exist yet.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import helpers — support hyphenated filenames
# ---------------------------------------------------------------------------

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "vision"


def _import_hyphen_module(name: str, path: Path):
    """Load a module from a file path (handles hyphens in filename)."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# Import tense_gate (filename: tense-gate.py)
tense_gate = _import_hyphen_module("tense_gate", SCRIPTS_DIR / "tense-gate.py")

from scripts.vision_renderer import VisionAnswers, render_vision, render_genesis_adr  # noqa: E402
from scripts.vision_conformance import ConformanceResult, check_conformance  # noqa: E402


# ---------------------------------------------------------------------------
# Shared fixture: minimal valid VisionAnswers
# ---------------------------------------------------------------------------

@pytest.fixture
def minimal_answers() -> VisionAnswers:
    """Return the smallest valid VisionAnswers (3 principles, all present-tense)."""
    return VisionAnswers(
        vision_statement="We deliver reliable infrastructure tooling for platform engineers.",
        target_group="Platform engineers at mid-size software companies.",
        core_need="Engineers need reproducible, auditable infrastructure changes without manual toil.",
        positioning=(
            "For platform teams drowning in config drift, "
            "our tooling provides automated enforcement that SaaS vendors cannot match."
        ),
        principles=[
            ("P1", "All infrastructure changes are applied through version-controlled manifests."),
            ("P2", "Every policy violation surfaces at plan time, not apply time."),
            ("P3", "Operators see full change context before confirming any action."),
        ],
        principle_scopes={
            "P1": "all infrastructure modules",
            "P2": "policy engine, CI pipelines",
            "P3": "operator CLI, dashboard",
        },
        business_goal="Reduce unplanned outages caused by config drift by 90% within six months of adoption.",
        not_in_vision=[
            "Auto-remediation without operator approval",
            "Support for non-declarative infrastructure tools",
        ],
    )


@pytest.fixture
def five_principle_answers(minimal_answers: VisionAnswers) -> VisionAnswers:
    """VisionAnswers with exactly 5 principles (upper boundary)."""
    principles = list(minimal_answers.principles) + [
        ("P4", "All secrets are injected at runtime and never stored in manifests."),
        ("P5", "The system emits a structured audit log for every change event."),
    ]
    scopes = dict(minimal_answers.principle_scopes)
    scopes["P4"] = "secrets management layer"
    scopes["P5"] = "audit subsystem"
    return VisionAnswers(
        vision_statement=minimal_answers.vision_statement,
        target_group=minimal_answers.target_group,
        core_need=minimal_answers.core_need,
        positioning=minimal_answers.positioning,
        principles=principles,
        principle_scopes=scopes,
        business_goal=minimal_answers.business_goal,
        not_in_vision=minimal_answers.not_in_vision,
    )


# ---------------------------------------------------------------------------
# Group 1: TestVisionRenderer
# ---------------------------------------------------------------------------

class TestVisionRenderer:
    """Tests for scripts/vision_renderer.py :: render_vision()."""

    def test_render_produces_all_7_sections(self, minimal_answers):
        """Rendered output must contain all 7 required H2 headers."""
        output = render_vision(minimal_answers)
        required_headers = [
            "## Vision Statement",
            "## Target Group",
            "## Core Need",
            "## Positioning",
            "## Value Principles",
            "## Business Goal",
            "## NOT in Vision",
        ]
        for header in required_headers:
            assert header in output, f"Missing section header: {header!r}"

    def test_render_boundary_table_has_4_columns(self, minimal_answers):
        """Each data row in the boundary table must have 4 pipe-delimited columns."""
        output = render_vision(minimal_answers)
        lines = output.splitlines()
        # Find lines that look like table data rows (not separator rows)
        data_rows = [
            ln for ln in lines
            if ln.startswith("|") and not all(c in "-|: " for c in ln.strip())
            and not ln.strip().startswith("| rule_id")  # skip header
        ]
        assert len(data_rows) >= 3, "Expected at least 3 boundary table data rows"
        for row in data_rows:
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            assert len(cells) == 4, f"Expected 4 columns in row, got {len(cells)}: {row!r}"

    def test_render_rejects_vision_statement_over_30_words(self):
        """vision_statement longer than 30 words must raise ValueError."""
        long_statement = " ".join(["word"] * 31)
        answers = VisionAnswers(
            vision_statement=long_statement,
            target_group="Target.",
            core_need="Need.",
            positioning="Positioning.",
            principles=[
                ("P1", "Boundaries are enforced at commit time."),
                ("P2", "Rules are expressed once and reused everywhere."),
                ("P3", "Violations surface in the developer workflow."),
            ],
            principle_scopes={"P1": "all", "P2": "all", "P3": "all"},
            business_goal="Goal.",
            not_in_vision=["Item one", "Item two"],
        )
        with pytest.raises(ValueError, match="30"):
            render_vision(answers)

    def test_render_rejects_too_few_principles(self):
        """Fewer than 3 principles must raise ValueError."""
        answers = VisionAnswers(
            vision_statement="Short valid statement for testing purposes.",
            target_group="Target group.",
            core_need="Core need.",
            positioning="Positioning statement.",
            principles=[
                ("P1", "One principle only."),
                ("P2", "Two principles only."),
            ],
            principle_scopes={"P1": "all", "P2": "all"},
            business_goal="Business goal.",
            not_in_vision=["Deferred item"],
        )
        with pytest.raises(ValueError, match="[Pp]rinciple"):
            render_vision(answers)

    def test_render_rejects_too_many_principles(self):
        """More than 5 principles must raise ValueError."""
        principles = [(f"P{i}", f"Principle number {i} stated in present tense.") for i in range(1, 7)]
        scopes = {f"P{i}": "all" for i in range(1, 7)}
        answers = VisionAnswers(
            vision_statement="Short valid statement for testing.",
            target_group="Target group.",
            core_need="Core need.",
            positioning="Positioning statement.",
            principles=principles,
            principle_scopes=scopes,
            business_goal="Business goal.",
            not_in_vision=["Deferred item"],
        )
        with pytest.raises(ValueError, match="[Pp]rinciple"):
            render_vision(answers)

    def test_render_golden_file(self, minimal_answers, tmp_path):
        """Render minimal_answers and verify key structural properties (golden-file style)."""
        output = render_vision(minimal_answers)
        # Write to a file to simulate golden output
        golden = tmp_path / "vision.md"
        golden.write_text(output, encoding="utf-8")

        # Key invariants from the golden output
        assert "document_type: prescriptive-present" in output
        assert "template_version: 1" in output
        assert "generator: vision-author" in output
        # Vision statement content appears in output
        assert "platform engineers" in output.lower()
        # Principles appear as list items
        assert "- **P1**:" in output
        assert "- **P2**:" in output
        assert "- **P3**:" in output
        # Boundary table header
        assert "rule_id" in output
        assert "source-section" in output
        # NOT in Vision items
        assert "Auto-remediation" in output

    def test_render_includes_frontmatter(self, minimal_answers):
        """Rendered output must start with YAML frontmatter block."""
        output = render_vision(minimal_answers)
        assert output.startswith("---\n"), "Must start with YAML frontmatter delimiter"
        assert output.count("---") >= 2, "Must have opening and closing frontmatter delimiters"

    def test_render_source_section_is_value_principles(self, minimal_answers):
        """source-section column in boundary table must always be 'Value Principles'."""
        output = render_vision(minimal_answers)
        lines = output.splitlines()
        # Find boundary table data rows
        in_table = False
        for line in lines:
            if "| rule_id |" in line:
                in_table = True
                continue
            if in_table and line.startswith("|") and not all(c in "-|: " for c in line.strip()):
                # Data row
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) == 4:
                    assert cells[3] == "Value Principles", (
                        f"source-section must be 'Value Principles', got: {cells[3]!r}"
                    )
            elif in_table and not line.startswith("|"):
                in_table = False

    def test_render_principle_ids_match_boundary_rule_ids(self, minimal_answers, tmp_path):
        """Principle IDs in the list must match rule_ids in the boundary table."""
        from scripts.vision_parser import parse_vision
        output = render_vision(minimal_answers)
        vision_file = tmp_path / "vision.md"
        vision_file.write_text(output, encoding="utf-8")
        vision = parse_vision(vision_file)
        principle_ids = {p.id for p in vision.principles}
        boundary_ids = {br.rule_id for br in vision.boundary_table}
        assert principle_ids == boundary_ids

    def test_render_rejects_missing_principle_scope(self):
        """render_vision must raise ValueError if principle_scopes is missing an entry."""
        answers = VisionAnswers(
            vision_statement="We deliver reliable infrastructure tooling for platform engineers.",
            target_group="Platform engineers at mid-size companies.",
            core_need="Engineers need reproducible infrastructure changes without toil.",
            positioning="Automated enforcement for platform teams.",
            principles=[
                ("P1", "All infrastructure changes are version-controlled."),
                ("P2", "Every policy violation surfaces at plan time."),
                ("P3", "Operators see full change context before confirming."),
            ],
            principle_scopes={
                "P1": "all infrastructure modules",
                "P2": "policy engine, CI pipelines",
                # P3 intentionally omitted
            },
            business_goal="Reduce outages by 90% within six months.",
            not_in_vision=["Auto-remediation", "Non-declarative tools"],
        )
        with pytest.raises(ValueError, match="[Mm]issing scopes"):
            render_vision(answers)

    def test_render_5_principles_accepted(self, five_principle_answers):
        """Exactly 5 principles must be accepted without raising."""
        output = render_vision(five_principle_answers)
        assert "- **P5**:" in output

    def test_rendered_output_parseable_by_vision_parser(self, minimal_answers, tmp_path):
        """Rendered output must be parseable by vision_parser without errors."""
        from scripts.vision_parser import parse_vision, VisionParseError
        output = render_vision(minimal_answers)
        vision_file = tmp_path / "vision.md"
        vision_file.write_text(output, encoding="utf-8")
        vision = parse_vision(vision_file)
        assert vision.template_version == 1
        assert len(vision.principles) == 3


# ---------------------------------------------------------------------------
# Group 2: TestConformanceScanner
# ---------------------------------------------------------------------------

class TestConformanceScanner:
    """Tests for scripts/vision_conformance.py :: check_conformance()."""

    def test_valid_vision_is_conformant(self):
        """The existing valid.md fixture must report is_conformant=True."""
        result = check_conformance(FIXTURES_DIR / "valid.md")
        assert isinstance(result, ConformanceResult)
        assert result.is_conformant is True
        assert result.missing_sections == []
        assert result.has_boundary_table is True
        assert result.errors == []

    def test_missing_section_is_not_conformant(self):
        """missing_section.md fixture must report is_conformant=False."""
        result = check_conformance(FIXTURES_DIR / "missing_section.md")
        assert result.is_conformant is False
        # At least one missing section must be reported
        assert len(result.missing_sections) >= 1 or len(result.errors) >= 1

    def test_no_boundary_table_reports_error(self):
        """no_boundary_table.md fixture must report is_conformant=False and has_boundary_table=False."""
        result = check_conformance(FIXTURES_DIR / "no_boundary_table.md")
        assert result.is_conformant is False
        assert result.has_boundary_table is False

    def test_conformance_result_is_dataclass(self):
        """check_conformance must return a ConformanceResult dataclass."""
        result = check_conformance(FIXTURES_DIR / "valid.md")
        assert hasattr(result, "is_conformant")
        assert hasattr(result, "missing_sections")
        assert hasattr(result, "has_boundary_table")
        assert hasattr(result, "errors")

    def test_nonexistent_file_returns_not_conformant(self, tmp_path):
        """Nonexistent file must return is_conformant=False with error message."""
        result = check_conformance(tmp_path / "nonexistent.md")
        assert result.is_conformant is False
        assert len(result.errors) >= 1

    def test_missing_section_names_the_section(self):
        """missing_section.md conformance result must name the missing section."""
        result = check_conformance(FIXTURES_DIR / "missing_section.md")
        # The fixture is missing Business Goal
        all_messages = " ".join(result.missing_sections + result.errors).lower()
        assert "business goal" in all_messages or "business" in all_messages


# ---------------------------------------------------------------------------
# Group 3: TestTenseGateIntegration
# ---------------------------------------------------------------------------

class TestTenseGateIntegration:
    """Integration tests: rendered output vs tense-gate linter."""

    def test_rendered_output_passes_tense_gate(self, minimal_answers, tmp_path):
        """Rendering clean present-tense answers must produce 0 tense-gate violations."""
        output = render_vision(minimal_answers)
        vision_file = tmp_path / "vision.md"
        vision_file.write_text(output, encoding="utf-8")
        violations = tense_gate.lint_file(vision_file)
        assert violations == [], (
            f"Expected 0 violations, got {len(violations)}:\n"
            + "\n".join(f"  line {v[0]}: [{v[1]}] {v[3]}" for v in violations)
        )

    def test_future_tense_in_principle_fails_tense_gate(self, tmp_path):
        """A principle using 'will' must trigger tense-gate violations."""
        answers = VisionAnswers(
            vision_statement="We provide reliable tooling for teams.",
            target_group="Development teams.",
            core_need="Teams need reliable infrastructure.",
            positioning="Automated enforcement for modern teams.",
            principles=[
                ("P1", "The system will enforce boundaries at commit time."),  # future tense!
                ("P2", "Rules are expressed once and reused everywhere."),
                ("P3", "Violations surface in the developer workflow."),
            ],
            principle_scopes={"P1": "all", "P2": "all", "P3": "all"},
            business_goal="Reduce drift by 80% within six months.",
            not_in_vision=["Auto-remediation", "Non-declarative tools"],
        )
        output = render_vision(answers)
        vision_file = tmp_path / "vision.md"
        vision_file.write_text(output, encoding="utf-8")
        violations = tense_gate.lint_file(vision_file)
        assert len(violations) > 0, "Expected tense-gate violations for 'will enforce'"

    def test_stub_in_principle_fails_tense_gate(self, tmp_path):
        """A principle containing 'TBD' must trigger tense-gate violations."""
        answers = VisionAnswers(
            vision_statement="We provide reliable tooling for teams.",
            target_group="Development teams.",
            core_need="Teams need reliable infrastructure.",
            positioning="Automated enforcement for modern teams.",
            principles=[
                ("P1", "Boundaries are enforced at commit time."),
                ("P2", "Rules are expressed once and reused everywhere."),
                ("P3", "TBD - to be determined later."),  # stub!
            ],
            principle_scopes={"P1": "all", "P2": "all", "P3": "all"},
            business_goal="Reduce drift by 80% within six months.",
            not_in_vision=["Auto-remediation", "Non-declarative tools"],
        )
        output = render_vision(answers)
        vision_file = tmp_path / "vision.md"
        vision_file.write_text(output, encoding="utf-8")
        violations = tense_gate.lint_file(vision_file)
        assert len(violations) > 0, "Expected tense-gate violations for 'TBD'"


# ---------------------------------------------------------------------------
# Group 4: TestRefreshModeConformance
# ---------------------------------------------------------------------------

class TestRefreshModeConformance:
    """Tests for --refresh mode: conformance scanning before loading defaults."""

    def test_refresh_on_valid_file_returns_conformant(self):
        """A fully valid vision.md passes the pre-refresh conformance check."""
        result = check_conformance(FIXTURES_DIR / "valid.md")
        assert result.is_conformant is True

    def test_refresh_on_missing_section_returns_not_conformant(self):
        """A vision.md with missing sections fails the pre-refresh conformance check."""
        result = check_conformance(FIXTURES_DIR / "missing_section.md")
        assert result.is_conformant is False

    def test_refresh_on_bad_boundary_table_returns_not_conformant(self):
        """A vision.md with a bad boundary table fails the pre-refresh conformance check."""
        result = check_conformance(FIXTURES_DIR / "bad_boundary_table.md")
        assert result.is_conformant is False

    def test_refresh_conformance_reports_all_seven_sections_present_for_valid(self):
        """Valid fixture must show 0 missing sections."""
        result = check_conformance(FIXTURES_DIR / "valid.md")
        assert result.missing_sections == []

    def test_conformance_errors_are_strings(self):
        """errors field must be a list of strings."""
        result = check_conformance(FIXTURES_DIR / "missing_section.md")
        for err in result.errors:
            assert isinstance(err, str)

    def test_conformance_missing_sections_are_strings(self):
        """missing_sections field must be a list of strings."""
        result = check_conformance(FIXTURES_DIR / "missing_section.md")
        for section in result.missing_sections:
            assert isinstance(section, str)


# ---------------------------------------------------------------------------
# Group 5: TestGenesisADR
# ---------------------------------------------------------------------------

class TestGenesisADR:
    """Tests for scripts/vision_renderer.py :: render_genesis_adr()."""

    def test_render_genesis_adr_contains_required_sections(self):
        """render_genesis_adr must produce an ADR with all required sections and markers."""
        output = render_genesis_adr("my-project", "2026-04-22")
        assert "# ADR-0000" in output, "Must contain '# ADR-0000' heading"
        assert "**Status:** accepted" in output, "Must contain accepted status"
        assert "## Context" in output, "Must contain Context section"
        assert "## Decision" in output, "Must contain Decision section"
        assert "## Consequences" in output, "Must contain Consequences section"
        assert "generator: vision-author" in output, "Must contain generator marker"
