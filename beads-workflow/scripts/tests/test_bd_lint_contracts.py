#!/usr/bin/env python3
"""Tests for bd-lint-contracts.py — fixture-based, no real bd calls.

Run with:
    python -m pytest beads-workflow/scripts/tests/test_bd_lint_contracts.py -v
or:
    python beads-workflow/scripts/tests/test_bd_lint_contracts.py
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts directory to path so we can import the linter
SCRIPTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import bd_lint_contracts as linter

# ---------------------------------------------------------------------------
# Fixtures — pure Python strings representing bead descriptions
# ---------------------------------------------------------------------------

GOOD_DESCRIPTION = """\
## Summary
This bead implements an ADR-backed feature.

## Architecture Contracts Touched
- ADR-001 (TypedIDs): This bead uses typed ID helpers throughout the adapter layer.
- Helper: lib/id-helpers.ts
- Enforcer-Reactive: eslint/no-raw-id-concat

## Coverage Expected
- Packages: lib/adapters, lib/core
- Status nach Bead: ADR-001 column turns green in the matrix

## Gaps to Close
- [ ] None
"""

GOOD_DESCRIPTION_MULTIPLE_GAPS = """\
## Architecture Contracts Touched
- ADR-002 (EntityBoundary): Wraps all cross-module calls in boundary helpers.
- Enforcer-Proactive: scripts/gen-boundary.ts

## Coverage Expected
- Packages: lib/boundary

## Gaps to Close
- [ ] [ADR-NEEDED] Document the boundary crossing rules formally
- [ ] [ENFORCER-REACTIVE-NEEDED] Add lint rule for direct cross-module imports
"""

GOOD_DESCRIPTION_EXPLICIT_NO_GAPS = """\
## Architecture Contracts Touched
- ADR-003 (EventSourcing): Records all state changes as domain events.

## Gaps to Close
- [ ] None
"""

BAD_3A_EMPTY_SECTION = """\
## Architecture Contracts Touched

## Coverage Expected
- Packages: lib/core

## Gaps to Close
- [ ] None
"""

BAD_3A_WHITESPACE_ONLY = """\
## Architecture Contracts Touched


## Gaps to Close
- [ ] None
"""

BAD_3B_NO_ADR_BULLET = """\
## Architecture Contracts Touched
- Helper: lib/some-helper.ts
- Enforcer-Reactive: eslint/some-rule

## Gaps to Close
- [ ] None
"""

BAD_3B_WRONG_ADR_FORMAT = """\
## Architecture Contracts Touched
- ADR001 TypedIDs: missing hyphen and parens format
- Helper: lib/id-helpers.ts

## Gaps to Close
- [ ] None
"""

BAD_3C_NO_GAPS_SECTION = """\
## Architecture Contracts Touched
- ADR-001 (TypedIDs): Uses typed ID helpers.

## Coverage Expected
- Packages: lib/core
"""

BAD_3C_EMPTY_GAPS = """\
## Architecture Contracts Touched
- ADR-001 (TypedIDs): Uses typed ID helpers.

## Gaps to Close

## Next Steps
- Deploy to staging
"""

BAD_3C_INVALID_BULLETS = """\
## Architecture Contracts Touched
- ADR-001 (TypedIDs): Uses typed ID helpers.

## Gaps to Close
- No gaps identified
- Everything is fine
"""

BAD_3C_CHECKBOX_NO_KEYWORD = """\
## Architecture Contracts Touched
- ADR-001 (TypedIDs): Uses typed ID helpers.

## Gaps to Close
- [ ] We should look into this later
- [ ] Also consider the boundary issue
"""

EDGE_OPTIONAL_ONLY_NO_ADR = """\
## Architecture Contracts Touched
- Helper: lib/helper.ts
- Enforcer-Proactive: scripts/gen.ts
- Enforcer-Reactive: eslint/rule

## Gaps to Close
- [ ] None
"""

NO_CONTRACT_SECTION = """\
## Summary
This bead has no architectural contracts.

## Acceptance Criteria
- [ ] Works correctly
"""

# ---------------------------------------------------------------------------
# Tests for extract_section()
# ---------------------------------------------------------------------------

class TestExtractSection(unittest.TestCase):

    def test_extracts_existing_section(self):
        result = linter.extract_section(GOOD_DESCRIPTION, "## Architecture Contracts Touched")
        self.assertIsNotNone(result)
        self.assertIn("ADR-001", result)

    def test_returns_none_for_missing_section(self):
        result = linter.extract_section(NO_CONTRACT_SECTION, "## Architecture Contracts Touched")
        self.assertIsNone(result)

    def test_does_not_include_next_header(self):
        result = linter.extract_section(GOOD_DESCRIPTION, "## Architecture Contracts Touched")
        self.assertNotIn("## Coverage Expected", result)

    def test_extracts_gaps_section(self):
        result = linter.extract_section(GOOD_DESCRIPTION, "## Gaps to Close")
        self.assertIsNotNone(result)
        self.assertIn("None", result)

    def test_handles_section_at_end_of_document(self):
        result = linter.extract_section(GOOD_DESCRIPTION_EXPLICIT_NO_GAPS, "## Gaps to Close")
        self.assertIsNotNone(result)
        self.assertIn("None", result)


# ---------------------------------------------------------------------------
# Tests for validate_contracts_section()
# ---------------------------------------------------------------------------

class TestValidateContractsSection(unittest.TestCase):

    def test_good_description_no_errors(self):
        errors = linter.validate_contracts_section("BEAD-001", GOOD_DESCRIPTION)
        self.assertEqual(errors, [], f"Expected no errors, got: {errors}")

    def test_good_multiple_gaps_no_errors(self):
        errors = linter.validate_contracts_section("BEAD-002", GOOD_DESCRIPTION_MULTIPLE_GAPS)
        self.assertEqual(errors, [])

    def test_good_explicit_no_gaps_no_errors(self):
        errors = linter.validate_contracts_section("BEAD-003", GOOD_DESCRIPTION_EXPLICIT_NO_GAPS)
        self.assertEqual(errors, [])

    def test_no_section_returns_no_errors(self):
        # If there's no section at all, no contract errors (label check is separate)
        errors = linter.validate_contracts_section("BEAD-000", NO_CONTRACT_SECTION)
        self.assertEqual(errors, [])

    # Rule 3a tests
    def test_3a_empty_section_fails(self):
        errors = linter.validate_contracts_section("BEAD-3A", BAD_3A_EMPTY_SECTION)
        self.assertTrue(any("3a" in e.rule or "empty" in e.message.lower() for e in errors),
                        f"Expected rule 3a error, got: {errors}")

    def test_3a_whitespace_only_fails(self):
        errors = linter.validate_contracts_section("BEAD-3AW", BAD_3A_WHITESPACE_ONLY)
        self.assertTrue(any("3a" in e.rule or "empty" in e.message.lower() for e in errors),
                        f"Expected rule 3a error, got: {errors}")

    # Rule 3b tests
    def test_3b_no_adr_bullet_fails(self):
        errors = linter.validate_contracts_section("BEAD-3B", BAD_3B_NO_ADR_BULLET)
        self.assertTrue(any("3b" in e.rule or "ADR" in e.message for e in errors),
                        f"Expected rule 3b error, got: {errors}")

    def test_3b_wrong_adr_format_fails(self):
        errors = linter.validate_contracts_section("BEAD-3BF", BAD_3B_WRONG_ADR_FORMAT)
        self.assertTrue(any("3b" in e.rule or "ADR" in e.message for e in errors),
                        f"Expected rule 3b format error, got: {errors}")

    def test_3b_edge_optional_only_fails(self):
        # Section with only Helper/Enforcer bullets but no ADR bullet → error
        errors = linter.validate_contracts_section("BEAD-EDGE", EDGE_OPTIONAL_ONLY_NO_ADR)
        self.assertTrue(any("3b" in e.rule or "ADR" in e.message for e in errors),
                        f"Expected rule 3b error for optional-only section, got: {errors}")

    # Rule 3c tests
    def test_3c_no_gaps_section_fails(self):
        errors = linter.validate_contracts_section("BEAD-3C", BAD_3C_NO_GAPS_SECTION)
        self.assertTrue(any("3c" in e.rule or "Gaps" in e.message for e in errors),
                        f"Expected rule 3c error, got: {errors}")

    def test_3c_empty_gaps_fails(self):
        errors = linter.validate_contracts_section("BEAD-3CE", BAD_3C_EMPTY_GAPS)
        self.assertTrue(any("3c" in e.rule or "Gaps" in e.message for e in errors),
                        f"Expected rule 3c empty error, got: {errors}")

    def test_3c_invalid_bullets_fails(self):
        errors = linter.validate_contracts_section("BEAD-3CI", BAD_3C_INVALID_BULLETS)
        self.assertTrue(any("3c" in e.rule or "Gaps" in e.message or "valid" in e.message.lower() for e in errors),
                        f"Expected rule 3c invalid bullets error, got: {errors}")

    def test_3c_checkbox_no_keyword_fails(self):
        errors = linter.validate_contracts_section("BEAD-3CK", BAD_3C_CHECKBOX_NO_KEYWORD)
        self.assertTrue(any("3c" in e.rule or "valid" in e.message.lower() or "pattern" in e.message.lower() for e in errors),
                        f"Expected rule 3c keyword error, got: {errors}")

    def test_error_contains_bead_id(self):
        errors = linter.validate_contracts_section("MY-BEAD-ID", BAD_3A_EMPTY_SECTION)
        for e in errors:
            self.assertIn("MY-BEAD-ID", e.bead_id,
                          f"Error should reference bead ID, got: {e}")


# ---------------------------------------------------------------------------
# Tests for LintError dataclass
# ---------------------------------------------------------------------------

class TestLintError(unittest.TestCase):

    def test_lint_error_has_required_fields(self):
        err = linter.LintError(bead_id="X-001", rule="3a", message="test message")
        self.assertEqual(err.bead_id, "X-001")
        self.assertEqual(err.rule, "3a")
        self.assertEqual(err.message, "test message")

    def test_lint_error_str_contains_all_parts(self):
        err = linter.LintError(bead_id="X-001", rule="3b", message="missing ADR bullet")
        s = str(err)
        self.assertIn("X-001", s)
        self.assertIn("3b", s)
        self.assertIn("missing ADR bullet", s)


# ---------------------------------------------------------------------------
# Tests for check_false_negatives() — label false-negative check (Y)
# ---------------------------------------------------------------------------

class TestFalseNegatives(unittest.TestCase):

    def _make_bead(self, bead_id: str, description: str, has_label: bool) -> dict:
        return {
            "id": bead_id,
            "description": description,
            "labels": ["touches-contract"] if has_label else [],
        }

    def test_no_false_negatives_when_consistent(self):
        beads = [
            self._make_bead("B-001", GOOD_DESCRIPTION, True),
            self._make_bead("B-002", NO_CONTRACT_SECTION, False),
        ]
        errors = linter.check_false_negatives(beads)
        self.assertEqual(errors, [])

    def test_detects_section_without_label(self):
        beads = [
            self._make_bead("B-003", GOOD_DESCRIPTION, False),  # has section, missing label
        ]
        errors = linter.check_false_negatives(beads)
        self.assertTrue(len(errors) > 0, "Should detect section without label")
        self.assertTrue(any("label" in e.message.lower() or "touches-contract" in e.message for e in errors),
                        f"Error should mention label, got: {errors}")
        self.assertEqual(errors[0].bead_id, "B-003")

    def test_no_error_when_no_section_no_label(self):
        beads = [
            self._make_bead("B-004", NO_CONTRACT_SECTION, False),
        ]
        errors = linter.check_false_negatives(beads)
        self.assertEqual(errors, [])

    def test_no_error_when_label_and_section_present(self):
        beads = [
            self._make_bead("B-005", GOOD_DESCRIPTION, True),
        ]
        errors = linter.check_false_negatives(beads)
        self.assertEqual(errors, [])


# ---------------------------------------------------------------------------
# Tests for lint_bead() — mocking bd CLI calls
# ---------------------------------------------------------------------------

class TestLintBead(unittest.TestCase):

    def _mock_bd_show(self, description: str, labels: list[str]) -> MagicMock:
        """Create a mock for subprocess.run that simulates bd show output."""
        bead_data = [{
            "id": "TEST-001",
            "title": "Test Bead",
            "description": description,
            "labels": labels,
            "status": "open",
        }]
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = f'{{"id": "TEST-001", "description": {repr(description)}}}'
        return mock

    def test_lint_bead_good(self):
        bead_data = [{
            "id": "TEST-001",
            "title": "Test Bead",
            "description": GOOD_DESCRIPTION,
            "labels": ["touches-contract"],
            "status": "open",
        }]
        with patch("bd_lint_contracts._run") as mock_run:
            # bd show returns JSON
            mock_run.return_value = (0, f"[{{}}\n]", "")
            # Override with proper bead data
            mock_run.side_effect = [
                (0, __import__("json").dumps(bead_data), ""),  # bd show
                (0, "touches-contract", ""),                    # bd label list
            ]
            errors = linter.lint_bead("TEST-001")
            self.assertEqual(errors, [], f"Expected no errors for good bead, got: {errors}")

    def test_lint_bead_bad_no_label(self):
        bead_data = [{
            "id": "TEST-002",
            "title": "Test Bead",
            "description": GOOD_DESCRIPTION,  # has section
            "labels": [],                       # but no label → false negative
            "status": "open",
        }]
        with patch("bd_lint_contracts._run") as mock_run:
            mock_run.side_effect = [
                (0, __import__("json").dumps(bead_data), ""),  # bd show
                (0, "", ""),                                    # bd label list (no touches-contract)
            ]
            errors = linter.lint_bead("TEST-002")
            self.assertTrue(len(errors) > 0, "Should detect false negative")

    def test_lint_bead_bd_not_found(self):
        with patch("bd_lint_contracts._run") as mock_run:
            mock_run.return_value = (1, "", "bd: not found")
            errors = linter.lint_bead("MISSING-001")
            self.assertTrue(len(errors) > 0, "Should return error when bd not found")


# ---------------------------------------------------------------------------
# Integration-style tests for complete valid descriptions
# ---------------------------------------------------------------------------

class TestCompleteValidDescriptions(unittest.TestCase):

    def test_all_valid_fixtures_pass(self):
        valid_fixtures = [
            ("GOOD-001", GOOD_DESCRIPTION),
            ("GOOD-002", GOOD_DESCRIPTION_MULTIPLE_GAPS),
            ("GOOD-003", GOOD_DESCRIPTION_EXPLICIT_NO_GAPS),
        ]
        for bead_id, desc in valid_fixtures:
            with self.subTest(bead_id=bead_id):
                errors = linter.validate_contracts_section(bead_id, desc)
                self.assertEqual(errors, [],
                                 f"{bead_id}: Expected no errors, got: {errors}")

    def test_all_bad_fixtures_fail(self):
        bad_fixtures = [
            ("BAD-3A", BAD_3A_EMPTY_SECTION),
            ("BAD-3AW", BAD_3A_WHITESPACE_ONLY),
            ("BAD-3B", BAD_3B_NO_ADR_BULLET),
            ("BAD-3BF", BAD_3B_WRONG_ADR_FORMAT),
            ("BAD-3C", BAD_3C_NO_GAPS_SECTION),
            ("BAD-3CE", BAD_3C_EMPTY_GAPS),
            ("BAD-3CI", BAD_3C_INVALID_BULLETS),
            ("BAD-3CK", BAD_3C_CHECKBOX_NO_KEYWORD),
            ("EDGE", EDGE_OPTIONAL_ONLY_NO_ADR),
        ]
        for bead_id, desc in bad_fixtures:
            with self.subTest(bead_id=bead_id):
                errors = linter.validate_contracts_section(bead_id, desc)
                self.assertTrue(len(errors) > 0,
                                f"{bead_id}: Expected errors but got none")


if __name__ == "__main__":
    unittest.main(verbosity=2)
