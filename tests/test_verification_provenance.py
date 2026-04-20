"""
Tests for CCP-2vo.1 and CCP-2vo.9: verification-agent provenance contract.

Verifies:
1. verification-agent.md Input Contract contains all 4 provenance fields
2. bead-orchestrator.md Phase 4 template includes provenance fields
3. bead-orchestrator.md Phase 3.6 includes verification_tokens
4. update_verification_tokens() function exists and works
5. parse_usage() returns correct total for verification token capture

CCP-2vo.9 additions:
6. model upgraded to opus
7. THREE VETO checks (standards, ADR, docs) with fixability classification
8. ONE ADVISORY check (skills) with advisory-only output
9. Output Format updated with Provenance Compliance section
10. Information Barriers updated (old placeholder removed)
"""
import sys
from pathlib import Path
import sqlite3
import tempfile
import pytest

# Add lib path
LIB_PATH = Path(__file__).parent.parent / "beads-workflow" / "lib"
sys.path.insert(0, str(LIB_PATH))
from orchestrator.metrics import parse_usage, update_verification_tokens, init_db, insert_bead_run, BeadRun

AGENTS_DIR = Path(__file__).parent.parent / "beads-workflow" / "agents"
VERIFICATION_AGENT_MD = AGENTS_DIR / "verification-agent.md"
BEAD_ORCHESTRATOR_MD = AGENTS_DIR / "bead-orchestrator.md"


class TestProvenanceFieldsInVerificationAgent:
    def test_standards_applied_field_present(self):
        content = VERIFICATION_AGENT_MD.read_text()
        assert "standards_applied" in content

    def test_skills_referenced_field_present(self):
        content = VERIFICATION_AGENT_MD.read_text()
        assert "skills_referenced" in content

    def test_adrs_in_scope_field_present(self):
        content = VERIFICATION_AGENT_MD.read_text()
        assert "adrs_in_scope" in content

    def test_docs_required_field_present(self):
        content = VERIFICATION_AGENT_MD.read_text()
        assert "docs_required" in content


def phase4_section(content: str) -> str:
    """Return only the Phase 4: Completion Verification section of the orchestrator."""
    start = content.find("### Phase 4: Completion Verification")
    end = content.find("### Phase 4a:", start)
    return content[start:end] if start != -1 else ""


class TestProvenanceInOrchestrator:
    def test_phase4_template_contains_standards_applied(self):
        content = BEAD_ORCHESTRATOR_MD.read_text()
        assert "standards_applied" in phase4_section(content)

    def test_phase4_template_contains_skills_referenced(self):
        content = BEAD_ORCHESTRATOR_MD.read_text()
        assert "skills_referenced" in phase4_section(content)

    def test_phase4_template_contains_adrs_in_scope(self):
        content = BEAD_ORCHESTRATOR_MD.read_text()
        assert "adrs_in_scope" in phase4_section(content)

    def test_phase4_template_contains_docs_required(self):
        content = BEAD_ORCHESTRATOR_MD.read_text()
        assert "docs_required" in phase4_section(content)

    def test_phase36_references_verification_tokens(self):
        content = BEAD_ORCHESTRATOR_MD.read_text()
        assert "verification_tokens" in content

    def test_phase2_has_provenance_gathering_step(self):
        content = BEAD_ORCHESTRATOR_MD.read_text()
        assert "Provenance gathering" in content or "provenance" in content.lower()


class TestUpdateVerificationTokens:
    def test_update_verification_tokens_exists(self):
        # This test fails if the function doesn't exist
        from orchestrator.metrics import update_verification_tokens
        assert callable(update_verification_tokens)

    def test_update_verification_tokens_updates_db(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        try:
            conn = init_db(db_path)
            insert_bead_run(conn, BeadRun(bead_id="test-123", date="2026-04-20"))
            conn.close()
            update_verification_tokens("test-123", 42000, db_path=db_path)
            conn2 = sqlite3.connect(str(db_path))
            row = conn2.execute(
                "SELECT verification_tokens FROM bead_runs WHERE bead_id='test-123'"
            ).fetchone()
            conn2.close()
            assert row is not None
            assert row[0] == 42000
        finally:
            db_path.unlink(missing_ok=True)

    def test_update_verification_tokens_warns_when_no_row(self, capsys):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        try:
            init_db(db_path)  # initialize schema but don't insert any row
            update_verification_tokens("nonexistent-bead", 1000, db_path=db_path)
            captured = capsys.readouterr()
            assert "nonexistent-bead" in captured.err
        finally:
            db_path.unlink(missing_ok=True)

    def test_update_verification_tokens_updates_most_recent_row(self):
        """Verify that update_verification_tokens updates only the most recent row."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        try:
            conn = init_db(db_path)
            insert_bead_run(conn, BeadRun(bead_id="test-456", date="2026-04-19"))
            insert_bead_run(conn, BeadRun(bead_id="test-456", date="2026-04-20"))
            conn.close()
            update_verification_tokens("test-456", 99999, db_path=db_path)
            conn2 = sqlite3.connect(str(db_path))
            rows = conn2.execute(
                "SELECT id, verification_tokens FROM bead_runs WHERE bead_id='test-456' ORDER BY id ASC"
            ).fetchall()
            conn2.close()
            assert len(rows) == 2
            first_row_tokens = rows[0][1]
            second_row_tokens = rows[1][1]
            assert second_row_tokens == 99999, "Most recent (second) row should be updated"
            assert first_row_tokens == 0, "First row should remain untouched"
        finally:
            db_path.unlink(missing_ok=True)


class TestParseUsageForVerification:
    def test_parse_usage_extracts_total(self):
        response = """Some text before
<usage>{"input_tokens": 1000, "output_tokens": 500, "cache_creation_input_tokens": 200, "cache_read_input_tokens": 100}</usage>
Some text after"""
        result = parse_usage(response)
        assert result["total_tokens"] == 1800

    def test_parse_usage_returns_zeros_when_no_block(self):
        response = "Response with no usage block"
        result = parse_usage(response)
        assert result["total_tokens"] == 0

    def test_parse_usage_handles_malformed_json(self):
        response = "<usage>{not valid json}</usage>"
        result = parse_usage(response)
        assert result["total_tokens"] == 0

    def test_parse_usage_handles_triple_quotes_in_response(self):
        """parse_usage must survive triple-quote sequences in the response text.

        The orchestrator template previously embedded the response inside a Python
        triple-quoted string, so a '''  in SAW: output would cause a SyntaxError.
        The fix (temp-file pattern) avoids embedding entirely; this test verifies
        parse_usage itself is unaffected by such content regardless of the caller.
        """
        response = """Verification output with triple quotes: '''some code'''
<usage>{"input_tokens": 2000, "output_tokens": 300, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}</usage>
More text with $SHELL_VAR and `backticks` and "double quotes"."""
        result = parse_usage(response)
        assert result["total_tokens"] == 2300

    def test_parse_usage_handles_shell_metacharacters_in_response(self):
        """parse_usage must survive shell metacharacters that would break inline eval."""
        response = r"""Response containing $VAR $(subshell) `backtick` and \n newlines
<usage>{"input_tokens": 500, "output_tokens": 100, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}</usage>"""
        result = parse_usage(response)
        assert result["total_tokens"] == 600


# ---------------------------------------------------------------------------
# CCP-2vo.9: Provenance Compliance Checks
# ---------------------------------------------------------------------------


class TestModelUpgrade:
    def test_model_is_opus(self):
        content = VERIFICATION_AGENT_MD.read_text()
        assert "model: opus" in content


class TestVetoChecks:
    def test_standards_veto_section_present(self):
        content = VERIFICATION_AGENT_MD.read_text()
        assert "Standards Compliance Check" in content or "PROVENANCE-STANDARDS" in content

    def test_adr_veto_section_present(self):
        content = VERIFICATION_AGENT_MD.read_text()
        assert "ADR Compliance Check" in content or "PROVENANCE-ADR" in content

    def test_docs_existence_veto_section_present(self):
        content = VERIFICATION_AGENT_MD.read_text()
        assert "Docs-Existence Check" in content or "PROVENANCE-DOCS" in content

    def test_fixability_classification_present(self):
        content = VERIFICATION_AGENT_MD.read_text()
        assert "fixability: auto" in content
        assert "fixability: human" in content

    def test_veto_emits_disputed(self):
        content = VERIFICATION_AGENT_MD.read_text()
        assert "VERDICT: DISPUTED" in content

    def test_none_provenance_handled(self):
        content = VERIFICATION_AGENT_MD.read_text()
        assert "skipped" in content

    def test_scenario_standards_violation_to_disputed(self):
        """Spec must describe: standards violation → DISPUTED with fixability."""
        content = VERIFICATION_AGENT_MD.read_text()
        # Standards section must emit VERDICT: DISPUTED and classify fixability
        assert "PROVENANCE-STANDARDS" in content
        assert "VERDICT: DISPUTED" in content
        assert "fixability" in content

    def test_scenario_adr_contradiction_fixability_human(self):
        """Spec must describe: ADR violation → DISPUTED, fixability: human (as default)."""
        content = VERIFICATION_AGENT_MD.read_text()
        assert "PROVENANCE-ADR" in content
        # ADR violations are almost always fixability: human
        assert "fixability: human" in content

    def test_scenario_doc_missing_fixability_auto(self):
        """Spec must describe: missing doc → fixability: auto."""
        content = VERIFICATION_AGENT_MD.read_text()
        assert "PROVENANCE-DOCS" in content
        # Missing file gets auto fixability (scaffold can be generated)
        assert "fixability: auto" in content


class TestAdvisoryCheck:
    def test_advisory_section_present(self):
        content = VERIFICATION_AGENT_MD.read_text()
        assert "Skill Application Advisory" in content

    def test_advisory_likely_applied(self):
        content = VERIFICATION_AGENT_MD.read_text()
        assert "likely-applied" in content

    def test_advisory_unclear(self):
        content = VERIFICATION_AGENT_MD.read_text()
        assert "unclear" in content

    def test_advisory_no_evidence(self):
        content = VERIFICATION_AGENT_MD.read_text()
        assert "no-evidence" in content

    def test_advisory_not_veto(self):
        """Spec must say advisory never causes DISPUTED."""
        content = VERIFICATION_AGENT_MD.read_text()
        assert (
            "advisory-only" in content
            or "Do NOT emit DISPUTED" in content
            or "never causes DISPUTED" in content
        )

    def test_advisory_no_bd_update(self):
        """Spec must say agent does NOT call bd update."""
        content = VERIFICATION_AGENT_MD.read_text()
        assert "Do NOT call `bd update`" in content

    def test_scenario_skill_no_artifact_unclear(self):
        """Spec must describe: process-oriented skill with no diff artifact → unclear."""
        content = VERIFICATION_AGENT_MD.read_text()
        assert "unclear" in content
        # Must mention process-oriented or reasoning context
        assert "process" in content.lower() or "reasoning" in content.lower()

    def test_scenario_skill_absent_artifact_no_evidence(self):
        """Spec must describe: expected artifact absent from diff → no-evidence."""
        content = VERIFICATION_AGENT_MD.read_text()
        assert "no-evidence" in content
        assert "absent" in content or "ABSENT" in content or "not present" in content


class TestOutputFormatUpdated:
    def test_provenance_compliance_in_output_format(self):
        content = VERIFICATION_AGENT_MD.read_text()
        assert "Provenance Compliance" in content

    def test_status_rules_include_veto_disputed(self):
        """Status rules must mention that VETO or provenance DISPUTED affects overall status."""
        content = VERIFICATION_AGENT_MD.read_text()
        # Missing standard/ADR files now produce DISPUTED (not UNVERIFIABLE), which is a VETO violation
        assert "stale provenance paths are VETO violations" in content


class TestMissingFileFixability:
    def test_standards_missing_file_fixability_auto(self):
        content = VERIFICATION_AGENT_MD.read_text()
        # Find the file-not-found block for standards and confirm fixability: auto
        # Strategy: assert the spec contains the complete "file not found" + "fixability: auto" pattern
        assert "file not found" in content
        # Check that the block immediately following "file not found" for standards uses auto
        # Simple approach: check the phrase appears in context
        idx = content.find('file not found (provenance integrity warning)')
        assert idx != -1
        snippet = content[idx:idx+200]
        assert "fixability: auto" in snippet

    def test_adr_missing_file_fixability_auto(self):
        content = VERIFICATION_AGENT_MD.read_text()
        # Find the SECOND occurrence of "file not found" (ADR block)
        first = content.find('file not found (provenance integrity warning)')
        second = content.find('file not found (provenance integrity warning)', first + 1)
        assert second != -1, "Expected two file-not-found blocks (standards and ADR)"
        snippet = content[second:second+200]
        assert "fixability: auto" in snippet


class TestInformationBarriersUpdated:
    def test_old_placeholder_removed(self):
        """The old CCP-2vo.9 placeholder must be removed."""
        content = VERIFICATION_AGENT_MD.read_text()
        assert "reserved for CCP-2vo.9" not in content

    def test_no_fix_violations_barrier(self):
        """Information Barriers must say agent must not fix violations."""
        content = VERIFICATION_AGENT_MD.read_text()
        assert "Read-only verifier — classify fixability only" in content or "classify fixability only" in content
