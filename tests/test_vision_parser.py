#!/usr/bin/env python3
"""
Unit tests for scripts/vision_parser.py

Tests cover:
- Parsing a valid v1 vision.md fixture
- VisionParseError on missing required section
- VisionParseError on malformed boundary table
- Principle ID slug-stability (authored order preserved)
- Cross-reference validation (boundary rule_id must reference known principle)
- raw_text field preservation
"""

from pathlib import Path

import pytest

from scripts.vision_parser import VisionParseError, parse_vision


FIXTURES = Path(__file__).parent / "fixtures" / "vision"
VALID_FIXTURE = FIXTURES / "valid.md"
MISSING_SECTION_FIXTURE = FIXTURES / "missing_section.md"
BAD_BOUNDARY_FIXTURE = FIXTURES / "bad_boundary_table.md"


@pytest.fixture(scope="module")
def valid_vision():
    return parse_vision(VALID_FIXTURE)


class TestParseValidVision:
    """Test 1: parse_vision on valid fixture returns Vision dataclass with correct fields."""

    def test_returns_vision_dataclass(self, valid_vision):
        # Must return something non-None
        assert valid_vision is not None

    def test_vision_statement_is_non_empty(self, valid_vision):
        assert isinstance(valid_vision.vision_statement, str)
        assert len(valid_vision.vision_statement.strip()) > 0

    def test_principles_count(self, valid_vision):
        assert len(valid_vision.principles) >= 3

    def test_valid_fixture_has_one_boundary_rule_per_principle(self, valid_vision):
        # Each principle should have exactly one boundary rule
        assert len(valid_vision.boundary_table) == len(valid_vision.principles)

    def test_all_principle_ids_match_boundary_rule_ids(self, valid_vision):
        principle_ids = {p.id for p in valid_vision.principles}
        boundary_ids = {b.rule_id for b in valid_vision.boundary_table}
        assert principle_ids == boundary_ids

    def test_template_version(self, valid_vision):
        assert valid_vision.template_version == 1


class TestMissingSection:
    """Test 2: missing required section raises VisionParseError with line info."""

    def test_raises_vision_parse_error(self):
        with pytest.raises(VisionParseError):
            parse_vision(MISSING_SECTION_FIXTURE)

    def test_error_has_line_info(self):
        with pytest.raises(VisionParseError) as exc_info:
            parse_vision(MISSING_SECTION_FIXTURE)
        error = exc_info.value
        assert hasattr(error, "line")
        assert error.line > 0

    def test_error_message_is_actionable(self):
        with pytest.raises(VisionParseError) as exc_info:
            parse_vision(MISSING_SECTION_FIXTURE)
        error_str = str(exc_info.value)
        # The fixture is missing the "Business Goal" section — the error must name it
        assert "business goal" in error_str.lower()


class TestBadBoundaryTable:
    """Test 3: bad boundary table raises VisionParseError."""

    def test_raises_vision_parse_error(self):
        with pytest.raises(VisionParseError):
            parse_vision(BAD_BOUNDARY_FIXTURE)

    def test_error_mentions_boundary_or_table(self):
        with pytest.raises(VisionParseError) as exc_info:
            parse_vision(BAD_BOUNDARY_FIXTURE)
        error_str = str(exc_info.value).lower()
        assert "boundary" in error_str or "table" in error_str or "column" in error_str


class TestPrincipleIdSlugStability:
    """Test 4: principle ID slug-stability (ordering in output matches authored IDs)."""

    def test_first_principle_is_p1(self, valid_vision):
        assert valid_vision.principles[0].id == "P1"

    def test_second_principle_is_p2(self, valid_vision):
        assert valid_vision.principles[1].id == "P2"

    def test_principle_ids_are_authored(self, valid_vision):
        ids = [p.id for p in valid_vision.principles]
        assert ids == ["P1", "P2", "P3"]


class TestBoundaryUnknownRuleId:
    """Test 5: boundary rule_id must reference known principle (cross-reference validation)."""

    def test_unknown_rule_id_raises(self, tmp_path: Path):
        # Create a vision.md with boundary table row having unknown rule_id "P99"
        content = """\
---
document_type: prescriptive-present
template_version: 1
generator: vision-author
---

## Vision Statement

We build great tools.

## Target Group

Developers on long-lived codebases.

## Core Need (JTBD)

Teams need architectural quality without manual review.

## Positioning

Our tool provides automated enforcement with zero config.

## Value Principles

- **P1**: Boundaries are enforced at commit time.

| rule_id | rule | scope | source-section |
|---------|------|-------|----------------|
| P99 | Unknown rule | unknown scope | Value Principles |

## Business Goal

Reduce drift by 80%.

## NOT in Vision

- Auto-fixing violations.
"""
        vision_file = tmp_path / "vision.md"
        vision_file.write_text(content, encoding="utf-8")

        with pytest.raises(VisionParseError) as exc_info:
            parse_vision(vision_file)
        error_str = str(exc_info.value).lower()
        assert "p99" in error_str or "unknown" in error_str or "principle" in error_str

    def test_mismatched_boundary_raises(self, tmp_path: Path):
        """Boundary rule referencing P2 when only P1 exists should raise."""
        content = """\
---
document_type: prescriptive-present
template_version: 1
generator: vision-author
---

## Vision Statement

We build great tools.

## Target Group

Developers.

## Core Need (JTBD)

Architectural quality.

## Positioning

Automated enforcement.

## Value Principles

- **P1**: Rule one.

| rule_id | rule | scope | source-section |
|---------|------|-------|----------------|
| P2 | Mismatched rule | scope | Value Principles |

## Business Goal

Reduce drift.

## NOT in Vision

- Auto-fixing.
"""
        vision_file = tmp_path / "vision.md"
        vision_file.write_text(content, encoding="utf-8")

        with pytest.raises(VisionParseError):
            parse_vision(vision_file)


class TestPrinciplesAfterBoundaryTable:
    """Test 7: principles declared AFTER the boundary table are still collected."""

    def test_principle_after_table_is_collected(self, tmp_path: Path):
        """P4 declared after the boundary table must be parsed and not cause a cross-ref error."""
        content = """\
---
document_type: prescriptive-present
template_version: 1
generator: vision-author
---

## Vision Statement

We build great tools.

## Target Group

Developers on long-lived codebases.

## Core Need (JTBD)

Teams need architectural quality without manual review.

## Positioning

Our tool provides automated enforcement with zero config.

## Value Principles

- **P1**: Boundaries are enforced at commit time.
- **P2**: Rules are expressed once.
- **P3**: Violations are shown in context.

| rule_id | rule | scope | source-section |
|---------|------|-------|----------------|
| P1 | Commit-time enforcement | git hooks | Value Principles |
| P2 | Single-source rules | all components | Value Principles |
| P3 | In-context violations | developer workflow | Value Principles |
| P4 | Post-table principle | full system | Value Principles |

- **P4**: A principle written after the boundary table.

## Business Goal

Reduce drift by 80%.

## NOT in Vision

- Auto-fixing violations.
"""
        vision_file = tmp_path / "vision.md"
        vision_file.write_text(content, encoding="utf-8")

        vision = parse_vision(vision_file)
        principle_ids = [p.id for p in vision.principles]
        assert "P4" in principle_ids, f"Expected P4 in principles, got: {principle_ids}"
        assert len(vision.principles) == 4
        assert len(vision.boundary_table) == 4


class TestRawTextPreserved:
    """Test 6: raw_text field contains full file content."""

    def test_raw_text_equals_file_content(self, valid_vision):
        expected = VALID_FIXTURE.read_text(encoding="utf-8")
        assert valid_vision.raw_text == expected

    def test_raw_text_is_non_empty(self, valid_vision):
        assert len(valid_vision.raw_text) > 0


class TestAllSectionsParsed:
    """Additional tests for complete section coverage."""

    def test_target_group_is_non_empty(self, valid_vision):
        assert isinstance(valid_vision.target_group, str)
        assert len(valid_vision.target_group.strip()) > 0

    def test_core_need_is_non_empty(self, valid_vision):
        assert isinstance(valid_vision.core_need, str)
        assert len(valid_vision.core_need.strip()) > 0

    def test_positioning_is_non_empty(self, valid_vision):
        assert isinstance(valid_vision.positioning, str)
        assert len(valid_vision.positioning.strip()) > 0

    def test_business_goal_is_non_empty(self, valid_vision):
        assert isinstance(valid_vision.business_goal, str)
        assert len(valid_vision.business_goal.strip()) > 0

    def test_not_in_vision_is_non_empty(self, valid_vision):
        assert isinstance(valid_vision.not_in_vision, str)
        assert len(valid_vision.not_in_vision.strip()) > 0

    def test_principle_text_is_non_empty(self, valid_vision):
        for p in valid_vision.principles:
            assert len(p.text.strip()) > 0

    def test_boundary_rule_fields(self, valid_vision):
        for br in valid_vision.boundary_table:
            assert len(br.rule_id.strip()) > 0
            assert len(br.rule.strip()) > 0
            assert len(br.scope.strip()) > 0
            assert len(br.source_section.strip()) > 0
