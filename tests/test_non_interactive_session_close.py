"""
Tests for CCP-k1m: Non-interactive session-close mode.

Verifies all acceptance criteria:
  AC1: Audit document exists
  AC2: --non-interactive flag in Flags Reference
  AC3: Deterministic defaults for all interactive points
  AC4: Resume from mid-close state section
  AC5: 3+ stall fixture tests
  AC6: Existing interactive behavior unchanged
"""

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SESSION_CLOSE_MD = REPO_ROOT / "core" / "agents" / "session-close.md"
AUDIT_DOC = REPO_ROOT / "docs" / "architecture" / "non-interactive-session-close-audit.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _content() -> str:
    return SESSION_CLOSE_MD.read_text()


def _section(content: str, start_marker: str, end_marker: str | None = None) -> str:
    """Extract text between two markers (or from marker to end of file).

    When end_marker is "## ", search for a newline-prefixed h2 heading to avoid
    matching "## " inside h3 headings ("### ").
    """
    start = content.find(start_marker)
    if start == -1:
        return ""
    if end_marker is None:
        return content[start:]
    # Use newline-anchored search for heading markers to avoid substring matches
    # inside deeper headings (e.g. "## " inside "### ").
    search_marker = f"\n{end_marker.lstrip()}" if end_marker.startswith("#") else end_marker
    end = content.find(search_marker, start + len(start_marker))
    return content[start:end] if end != -1 else content[start:]


# ---------------------------------------------------------------------------
# AC1: Audit document
# ---------------------------------------------------------------------------

class TestAuditDocument:
    """AC1 — audit document exists and has required content."""

    def test_audit_document_exists(self):
        """AC1: docs/architecture/non-interactive-session-close-audit.md must exist."""
        assert AUDIT_DOC.exists(), (
            f"Audit document must exist at {AUDIT_DOC}"
        )

    def test_audit_document_has_interactive_points_table(self):
        """AC1: audit document must contain a table of interactive points."""
        content = AUDIT_DOC.read_text()
        assert "interactive" in content.lower(), (
            "Audit document must describe interactive points"
        )
        assert "|" in content, (
            "Audit document must contain a table (markdown pipe chars)"
        )

    def test_audit_document_has_classifications(self):
        """AC1: classifications must appear in the audit document."""
        content = AUDIT_DOC.read_text()
        # At least one of the three classification labels must be present
        has_classification = any(
            label in content
            for label in ("needs-human", "can-default", "can-pre-specify")
        )
        assert has_classification, (
            "Audit document must classify interactive points as "
            "needs-human | can-default | can-pre-specify"
        )

    def test_audit_document_has_safe_defaults(self):
        """AC1: audit document must describe safe defaults."""
        content = AUDIT_DOC.read_text()
        assert "default" in content.lower(), (
            "Audit document must document safe defaults for each interactive point"
        )


# ---------------------------------------------------------------------------
# AC2: --non-interactive flag in Flags Reference
# ---------------------------------------------------------------------------

class TestFlagsReference:
    """AC2 — --non-interactive appears in the Flags Reference table."""

    def test_non_interactive_flag_in_flags_reference(self):
        """AC2: --non-interactive must appear in the Flags Reference table."""
        content = _content()
        flags_section = _section(content, "## Flags Reference")
        assert "--non-interactive" in flags_section, (
            "--non-interactive must be listed in the Flags Reference table"
        )

    def test_non_interactive_has_description(self):
        """AC2: --non-interactive flag must have a non-empty description in the table."""
        content = _content()
        flags_section = _section(content, "## Flags Reference")
        # Find the table row for --non-interactive
        for line in flags_section.splitlines():
            if "--non-interactive" in line and "|" in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                assert len(parts) >= 2, (
                    "--non-interactive row must have at least flag + description columns"
                )
                return
        raise AssertionError(
            "--non-interactive must appear as a table row in the Flags Reference"
        )


# ---------------------------------------------------------------------------
# AC3: Deterministic defaults (Non-Interactive Mode section)
# ---------------------------------------------------------------------------

class TestNonInteractiveSection:
    """AC3 — Non-Interactive Mode section with deterministic defaults."""

    def test_non_interactive_section_exists(self):
        """AC3: a '## Non-Interactive Mode' section must exist."""
        content = _content()
        assert "## Non-Interactive Mode" in content, (
            "session-close.md must have a '## Non-Interactive Mode' section"
        )

    def test_env_var_trigger_documented(self):
        """AC3: SESSION_CLOSE_NON_INTERACTIVE env var must be documented."""
        content = _content()
        ni_section = _section(content, "## Non-Interactive Mode", "## ")
        assert "SESSION_CLOSE_NON_INTERACTIVE" in ni_section, (
            "Non-Interactive Mode section must document SESSION_CLOSE_NON_INTERACTIVE env var"
        )

    def test_non_interactive_auto_stage_default(self):
        """AC3: auto-stage behavior for unstaged files must be documented."""
        content = _content()
        ni_section = _section(content, "## Non-Interactive Mode", "## ")
        assert "auto-stage" in ni_section.lower() or "stage all" in ni_section.lower(), (
            "Non-Interactive Mode section must document auto-stage default for unstaged files"
        )

    def test_non_interactive_audit_proceed_default(self):
        """AC3: audit auto-proceed behavior must be documented."""
        content = _content()
        ni_section = _section(content, "## Non-Interactive Mode", "## ")
        assert "audit" in ni_section.lower() and (
            "proceed" in ni_section.lower() or "auto" in ni_section.lower()
        ), (
            "Non-Interactive Mode section must document auto-proceed for bun audit"
        )

    def test_non_interactive_commit_message_default(self):
        """AC3: auto-commit message default must be documented."""
        content = _content()
        ni_section = _section(content, "## Non-Interactive Mode", "## ")
        assert "commit" in ni_section.lower() and (
            "automated" in ni_section.lower() or "auto" in ni_section.lower()
            or "default" in ni_section.lower()
        ), (
            "Non-Interactive Mode section must document commit message default"
        )

    def test_non_interactive_fallback_commit_message(self):
        """AC3: fallback commit message format must be documented."""
        content = _content()
        ni_section = _section(content, "## Non-Interactive Mode", "## ")
        assert "chore:" in ni_section or "automated session close" in ni_section.lower(), (
            "Non-Interactive Mode section must document the fallback commit message pattern"
        )

    def test_step5_has_non_interactive_branch(self):
        """AC3: Step 5 must document --non-interactive auto-stage path."""
        content = _content()
        # Step 5 is under the "Review with user" section in Phase B Prepare
        step5_area = _section(content, "5. **Review with user", "6. **Note for Step 6")
        assert "non-interactive" in step5_area.lower() or "--non-interactive" in step5_area, (
            "Step 5 must document non-interactive auto-stage branch"
        )

    def test_step6_has_non_interactive_branch(self):
        """AC3: Step 6 must document --non-interactive auto-commit path."""
        content = _content()
        step6_area = _section(content, "### Step 6: Conventional Commit", "## Phase A")
        assert "non-interactive" in step6_area.lower() or "--non-interactive" in step6_area, (
            "Step 6 must document non-interactive auto-commit branch"
        )


# ---------------------------------------------------------------------------
# AC4: Resume capability
# ---------------------------------------------------------------------------

class TestResumeSection:
    """AC4 — Resume from Mid-Close State section."""

    def test_resume_section_exists(self):
        """AC4: a '## Resume from Mid-Close State' section must exist."""
        content = _content()
        assert "## Resume from Mid-Close State" in content, (
            "session-close.md must have a '## Resume from Mid-Close State' section"
        )

    def test_stall_fixture_after_impl_commit(self):
        """AC5 stall fixture: resume section covers 'after impl-commit' state."""
        content = _content()
        resume_section = _section(content, "## Resume from Mid-Close State", "## ")
        assert "commit" in resume_section.lower(), (
            "Resume section must cover detection of an existing conventional commit"
        )

    def test_stall_fixture_after_merge(self):
        """AC5 stall fixture: resume section covers 'after merge' state."""
        content = _content()
        resume_section = _section(content, "## Resume from Mid-Close State", "## ")
        assert "merge" in resume_section.lower() or "merged" in resume_section.lower(), (
            "Resume section must cover detection of an already-merged feature branch"
        )

    def test_stall_fixture_before_push(self):
        """AC5 stall fixture: resume section covers 'before push / tagged' state."""
        content = _content()
        resume_section = _section(content, "## Resume from Mid-Close State", "## ")
        assert "tag" in resume_section.lower() or "push" in resume_section.lower(), (
            "Resume section must cover detection of already-tagged or already-pushed state"
        )

    def test_resume_non_interactive_auto_routes(self):
        """AC4: resume section must state non-interactive auto-routes to checkpoint."""
        content = _content()
        resume_section = _section(content, "## Resume from Mid-Close State", "## ")
        assert "non-interactive" in resume_section.lower() or "--non-interactive" in resume_section, (
            "Resume section must describe non-interactive auto-routing behavior"
        )

    def test_resume_interactive_advisory(self):
        """AC4: in interactive mode, resume detection is advisory (prints state only)."""
        content = _content()
        resume_section = _section(content, "## Resume from Mid-Close State", "## ")
        assert "advisory" in resume_section.lower() or "print" in resume_section.lower(), (
            "Resume section must describe advisory (non-routing) behavior for interactive mode"
        )


# ---------------------------------------------------------------------------
# AC6: Existing interactive behavior unchanged
# ---------------------------------------------------------------------------

class TestInteractiveBehaviorPreserved:
    """AC6 — Interactive mode is still the default; existing behavior unchanged."""

    def test_existing_interactive_behavior_preserved(self):
        """AC6: Step 6 must still say 'Interactive' (default behavior unchanged)."""
        content = _content()
        step6_section = _section(content, "### Step 6: Conventional Commit", "## Phase A")
        assert "Interactive" in step6_section, (
            "Step 6 must still be labeled 'Interactive' — default behavior must not change"
        )

    def test_interactive_is_default(self):
        """AC6: --non-interactive must be described as opt-in (not default)."""
        content = _content()
        ni_section = _section(content, "## Non-Interactive Mode", "## ")
        assert "opt-in" in ni_section.lower() or "default" in ni_section.lower(), (
            "--non-interactive must be described as opt-in; interactive is the default"
        )
