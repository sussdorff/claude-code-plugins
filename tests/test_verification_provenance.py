"""
Tests for CCP-2vo.1: verification-agent provenance contract.

Verifies:
1. verification-agent.md Input Contract contains all 4 provenance fields
2. bead-orchestrator.md Phase 4 template includes provenance fields
3. bead-orchestrator.md Phase 3.6 includes verification_tokens
4. update_verification_tokens() function exists and works
5. parse_usage() returns correct total for verification token capture
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
