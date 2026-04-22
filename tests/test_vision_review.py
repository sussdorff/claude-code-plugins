#!/usr/bin/env python3
"""
Unit tests for scripts/vision_review.py

Tests cover:
- Health score calculation (golden-file style unit tests)
- Draft ADR generation (file creation, frontmatter, supersedes field uses rule_id)
- Review report generation (council_mode, health_score fields)
- Health score < 80% triggers re-author suggestion
- Mock council smoke test (CLI --mock-council --yes exits 0)
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Ensure repo root is on sys.path (conftest.py does this, but be explicit)
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.vision_review import (
    PrincipleResult,
    compute_health_score,
    generate_draft_adr,
    generate_review_report,
)
from scripts.vision_parser import Principle

FIXTURES = Path(__file__).parent / "fixtures"
VISION_FIXTURE = FIXTURES / "vision" / "valid.md"
MOCK_COUNCIL_FIXTURE = FIXTURES / "vision-review" / "mock_council.json"


# ---------------------------------------------------------------------------
# Health score tests (golden-file style)
# ---------------------------------------------------------------------------

class TestComputeHealthScore:
    """Test 1-3: compute_health_score golden-file unit tests."""

    def test_two_of_three_confirmed(self):
        """compute_health_score(["P1", "P2"], 3) == 66.67"""
        score = compute_health_score(["P1", "P2"], 3)
        assert abs(score - 66.67) < 0.01, f"Expected 66.67, got {score}"

    def test_all_confirmed(self):
        """compute_health_score(["P1", "P2", "P3"], 3) == 100.0"""
        score = compute_health_score(["P1", "P2", "P3"], 3)
        assert score == 100.0, f"Expected 100.0, got {score}"

    def test_none_confirmed(self):
        """compute_health_score([], 3) == 0.0"""
        score = compute_health_score([], 3)
        assert score == 0.0, f"Expected 0.0, got {score}"

    def test_zero_total_returns_zero(self):
        """compute_health_score([], 0) == 0.0 (no division by zero)"""
        score = compute_health_score([], 0)
        assert score == 0.0

    def test_one_of_one(self):
        """compute_health_score(["P1"], 1) == 100.0"""
        score = compute_health_score(["P1"], 1)
        assert score == 100.0


# ---------------------------------------------------------------------------
# Draft ADR generation tests
# ---------------------------------------------------------------------------

class TestGenerateDraftAdr:
    """Test 4-5: generate_draft_adr creates file at expected path with correct frontmatter."""

    @pytest.fixture
    def principle(self):
        return Principle(id="P1", text="All architectural boundaries are enforced at commit time.")

    @pytest.fixture
    def adr_dir(self, tmp_path):
        d = tmp_path / "adr-drafts"
        d.mkdir(parents=True)
        return d

    def test_adr_file_created(self, principle, adr_dir):
        """generate_draft_adr() creates a file in the adr_dir."""
        path = generate_draft_adr(
            principle=principle,
            evidence="New deployment model changes when boundaries can be checked.",
            council_finding=None,
            run_date="20260422-120000",
            adr_dir=adr_dir,
        )
        assert path.exists(), f"Expected ADR file at {path}"

    def test_adr_filename_contains_rule_id(self, principle, adr_dir):
        """ADR filename includes the rule_id (P1), not a positional index."""
        path = generate_draft_adr(
            principle=principle,
            evidence="Evidence text.",
            council_finding=None,
            run_date="20260422-120000",
            adr_dir=adr_dir,
        )
        assert "P1" in path.name, f"Expected 'P1' in filename, got: {path.name}"
        assert "principle-0" not in path.name, "Filename must not use positional index"

    def test_adr_supersedes_uses_rule_id(self, principle, adr_dir):
        """Draft ADR frontmatter has 'supersedes: vision.md#P1' (rule_id), NOT positional index."""
        path = generate_draft_adr(
            principle=principle,
            evidence="Evidence text.",
            council_finding=None,
            run_date="20260422-120000",
            adr_dir=adr_dir,
        )
        content = path.read_text(encoding="utf-8")
        assert "supersedes: vision.md#P1" in content, (
            f"Expected 'supersedes: vision.md#P1' in ADR frontmatter.\nContent:\n{content}"
        )
        assert "supersedes: vision.md#principle-0" not in content, (
            "Must not use positional index in supersedes field"
        )

    def test_adr_frontmatter_type_field(self, principle, adr_dir):
        """ADR frontmatter has 'type: vision-mutation'."""
        path = generate_draft_adr(
            principle=principle,
            evidence="Evidence.",
            council_finding=None,
            run_date="20260422-120000",
            adr_dir=adr_dir,
        )
        content = path.read_text(encoding="utf-8")
        assert "type: vision-mutation" in content

    def test_adr_frontmatter_status_draft(self, principle, adr_dir):
        """ADR frontmatter has 'status: draft'."""
        path = generate_draft_adr(
            principle=principle,
            evidence="Evidence.",
            council_finding=None,
            run_date="20260422-120000",
            adr_dir=adr_dir,
        )
        content = path.read_text(encoding="utf-8")
        assert "status: draft" in content

    def test_adr_frontmatter_council_mode(self, principle, adr_dir):
        """ADR frontmatter has 'council_mode:' field."""
        path = generate_draft_adr(
            principle=principle,
            evidence="Evidence.",
            council_finding="Council says no issues.",
            run_date="20260422-120000",
            adr_dir=adr_dir,
        )
        content = path.read_text(encoding="utf-8")
        assert "council_mode:" in content

    def test_adr_architecture_contracts_section(self, principle, adr_dir):
        """ADR body has 'Architecture Contracts Touched' section with supersedes link."""
        path = generate_draft_adr(
            principle=principle,
            evidence="Evidence.",
            council_finding=None,
            run_date="20260422-120000",
            adr_dir=adr_dir,
        )
        content = path.read_text(encoding="utf-8")
        assert "Architecture Contracts Touched" in content
        assert "vision.md#P1" in content


# ---------------------------------------------------------------------------
# Review report generation tests
# ---------------------------------------------------------------------------

class TestGenerateReviewReport:
    """Test 6-9: generate_review_report creates report with correct fields."""

    @pytest.fixture
    def sample_results(self):
        return [
            PrincipleResult(
                principle_id="P1",
                principle_text="Boundaries at commit time.",
                confirmed=True,
                evidence="Still valid.",
                council_finding=None,
                council_mode="full",
            ),
            PrincipleResult(
                principle_id="P2",
                principle_text="Single-source rules.",
                confirmed=False,
                evidence="We now have multiple rule sources.",
                council_finding="Council concurs.",
                council_mode="full",
            ),
            PrincipleResult(
                principle_id="P3",
                principle_text="In-context violations.",
                confirmed=True,
                evidence="Still accurate.",
                council_finding=None,
                council_mode="full",
            ),
        ]

    def test_report_file_created(self, sample_results, tmp_path):
        """generate_review_report() creates a report file."""
        path = generate_review_report(
            vision_path=Path("docs/vision.md"),
            results=sample_results,
            health_score=66.67,
            council_mode="full",
            report_dir=tmp_path,
        )
        assert path.exists(), f"Expected report file at {path}"

    def test_report_has_council_mode(self, sample_results, tmp_path):
        """Report file contains 'council_mode: full|degraded'."""
        path = generate_review_report(
            vision_path=Path("docs/vision.md"),
            results=sample_results,
            health_score=66.67,
            council_mode="full",
            report_dir=tmp_path,
        )
        content = path.read_text(encoding="utf-8")
        assert "council_mode: full" in content, (
            f"Expected 'council_mode: full' in report.\nContent:\n{content}"
        )

    def test_report_has_health_score(self, sample_results, tmp_path):
        """Report file contains the health score value."""
        path = generate_review_report(
            vision_path=Path("docs/vision.md"),
            results=sample_results,
            health_score=66.67,
            council_mode="full",
            report_dir=tmp_path,
        )
        content = path.read_text(encoding="utf-8")
        assert "66" in content, f"Expected health score in report.\nContent:\n{content}"

    def test_report_low_score_triggers_reauthor_suggestion(self, tmp_path):
        """Health score < 80% triggers re-author suggestion in report."""
        results = [
            PrincipleResult(
                principle_id="P1",
                principle_text="Principle text.",
                confirmed=False,
                evidence="Outdated.",
                council_finding=None,
                council_mode="degraded",
            ),
        ]
        path = generate_review_report(
            vision_path=Path("docs/vision.md"),
            results=results,
            health_score=0.0,
            council_mode="degraded",
            report_dir=tmp_path,
        )
        content = path.read_text(encoding="utf-8")
        # Must mention re-author or vision-author
        assert "vision-author" in content.lower() or "re-author" in content.lower(), (
            f"Expected re-author suggestion for score < 80.\nContent:\n{content}"
        )

    def test_report_high_score_no_reauthor_warning(self, sample_results, tmp_path):
        """Health score >= 80% does NOT trigger re-author suggestion."""
        results = [
            PrincipleResult(
                principle_id="P1",
                principle_text="Principle.",
                confirmed=True,
                evidence="Valid.",
                council_finding=None,
                council_mode="full",
            ),
            PrincipleResult(
                principle_id="P2",
                principle_text="Principle 2.",
                confirmed=True,
                evidence="Valid.",
                council_finding=None,
                council_mode="full",
            ),
            PrincipleResult(
                principle_id="P3",
                principle_text="Principle 3.",
                confirmed=True,
                evidence="Valid.",
                council_finding=None,
                council_mode="full",
            ),
            PrincipleResult(
                principle_id="P4",
                principle_text="Principle 4.",
                confirmed=True,
                evidence="Valid.",
                council_finding=None,
                council_mode="full",
            ),
            PrincipleResult(
                principle_id="P5",
                principle_text="Principle 5.",
                confirmed=False,
                evidence="Slight concern.",
                council_finding=None,
                council_mode="full",
            ),
        ]
        # 4 of 5 = 80% exactly — should NOT trigger warning
        path = generate_review_report(
            vision_path=Path("docs/vision.md"),
            results=results,
            health_score=80.0,
            council_mode="full",
            report_dir=tmp_path,
        )
        content = path.read_text(encoding="utf-8")
        assert "vision-author --refresh" not in content, (
            "Should not suggest re-author at exactly 80%"
        )

    def test_report_degraded_mode_warning(self, tmp_path):
        """Report in degraded mode contains degraded-mode warning."""
        results = [
            PrincipleResult(
                principle_id="P1",
                principle_text="Principle.",
                confirmed=True,
                evidence="Still valid.",
                council_finding=None,
                council_mode="degraded",
            ),
        ]
        path = generate_review_report(
            vision_path=Path("docs/vision.md"),
            results=results,
            health_score=100.0,
            council_mode="degraded",
            report_dir=tmp_path,
        )
        content = path.read_text(encoding="utf-8")
        assert "degraded" in content.lower(), (
            f"Expected degraded mode warning.\nContent:\n{content}"
        )

    def test_report_document_type_in_frontmatter(self, sample_results, tmp_path):
        """Report frontmatter has 'document_type: vision-review'."""
        path = generate_review_report(
            vision_path=Path("docs/vision.md"),
            results=sample_results,
            health_score=66.67,
            council_mode="full",
            report_dir=tmp_path,
        )
        content = path.read_text(encoding="utf-8")
        assert "document_type: vision-review" in content


# ---------------------------------------------------------------------------
# Mock council smoke test
# ---------------------------------------------------------------------------

class TestMockCouncilSmoke:
    """Test 7: CLI with --mock-council and --yes exits 0."""

    def test_smoke_exits_zero(self, tmp_path):
        """python3 scripts/vision_review.py <valid.md> --mock-council <fixture> --yes exits 0."""
        adr_dir = tmp_path / "adr-drafts"
        adr_dir.mkdir()

        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).parent.parent / "scripts" / "vision_review.py"),
                str(VISION_FIXTURE),
                "--mock-council",
                str(MOCK_COUNCIL_FIXTURE),
                "--yes",
                "--output-dir",
                str(tmp_path),
                "--adr-dir",
                str(adr_dir),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"Expected exit 0.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_smoke_creates_report(self, tmp_path):
        """CLI smoke test creates a review report file."""
        adr_dir = tmp_path / "adr-drafts"
        adr_dir.mkdir()

        subprocess.run(
            [
                sys.executable,
                str(Path(__file__).parent.parent / "scripts" / "vision_review.py"),
                str(VISION_FIXTURE),
                "--mock-council",
                str(MOCK_COUNCIL_FIXTURE),
                "--yes",
                "--output-dir",
                str(tmp_path),
                "--adr-dir",
                str(adr_dir),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        # Find any generated vision-review file
        reports = list(tmp_path.glob("vision-review-*.md"))
        assert len(reports) >= 1, f"Expected at least one vision-review-*.md in {tmp_path}"

    def test_smoke_report_has_council_mode_field(self, tmp_path):
        """Smoke test report contains 'council_mode:' field."""
        adr_dir = tmp_path / "adr-drafts"
        adr_dir.mkdir()

        subprocess.run(
            [
                sys.executable,
                str(Path(__file__).parent.parent / "scripts" / "vision_review.py"),
                str(VISION_FIXTURE),
                "--mock-council",
                str(MOCK_COUNCIL_FIXTURE),
                "--yes",
                "--output-dir",
                str(tmp_path),
                "--adr-dir",
                str(adr_dir),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        reports = list(tmp_path.glob("vision-review-*.md"))
        assert reports, "No report file found"
        content = reports[0].read_text(encoding="utf-8")
        assert "council_mode:" in content, (
            f"Expected 'council_mode:' in report.\nContent:\n{content}"
        )
