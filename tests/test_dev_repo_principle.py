"""
Test: CCP-h8h — Dev-repo principle: this repo is dev-only, never a runtime source of truth.

Asserts that:
1. .agents/ is not committed (or gitignored so it cannot be re-introduced silently).
2. .codex/ is not committed (same reasoning).
3. No canonical source file references .agents/ or .codex/ as a required runtime path.
4. The architecture doc exists and declares the principle.
5. sync-codex-skills and sync-codex-agents write ONLY to user-scoped targets.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent
GITIGNORE = REPO_ROOT / ".gitignore"
ARCH_DOC = REPO_ROOT / "docs" / "architecture" / "dev-repo-principle.md"
SYNC_SKILLS = REPO_ROOT / "scripts" / "sync-codex-skills"
SYNC_AGENTS = REPO_ROOT / "scripts" / "sync-codex-agents"


class TestMirrorDirectoriesAbsent:
    """The in-repo mirror directories must not exist as committed content."""

    def test_agents_dir_not_committed(self) -> None:
        result = subprocess.run(
            ["git", "ls-files", ".agents/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.strip() == "", (
            ".agents/ must not contain any committed files. "
            "Run: git rm -r --cached .agents/ && rm -rf .agents/"
        )

    def test_codex_agents_not_committed(self) -> None:
        result = subprocess.run(
            ["git", "ls-files", ".codex/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.strip() == "", (
            ".codex/ must not contain any committed files. "
            "Run: git rm -r --cached .codex/ && rm -rf .codex/"
        )


class TestGitignoreProtectsAgainstReintroduction:
    """Once deleted, .agents/ and .codex/ must be gitignored so they cannot return silently."""

    def test_agents_dir_gitignored(self) -> None:
        content = GITIGNORE.read_text()
        assert ".agents/" in content or ".agents" in content, (
            ".agents/ must be in .gitignore to prevent silent re-introduction"
        )

    def test_codex_dir_gitignored(self) -> None:
        content = GITIGNORE.read_text()
        assert ".codex/" in content or ".codex" in content, (
            ".codex/ must be in .gitignore to prevent silent re-introduction"
        )


class TestNoCanonicalSourceRequiresMirrorPaths:
    """No canonical source file must reference .agents/ or .codex/ as a required runtime path.

    Allowed exceptions:
    - .gitignore (contains exclusion entries)
    - docs/architecture/dev-repo-principle.md (architectural explanation)
    - tests/test_dev_repo_principle.py (this file — asserts absence)
    - CHANGELOG.md (historical references)
    - docs/codex-skills-rollout-plan.md (superseded history)
    - docs/codex-agents.md (updated docs may still reference old paths in historical sections)
    """

    ALLOWED_FILES = {
        ".gitignore",
        "tests/test_dev_repo_principle.py",
        "tests/test_codex_pilot.py",            # mentions old paths in docstrings only
        "tests/test_codex_agents_sync.py",       # mentions old paths in docstrings only
        "tests/test_codex_agent_session_close.py",  # mentions old path in comment only
        "docs/architecture/dev-repo-principle.md",
        "CHANGELOG.md",
        "docs/codex-skills-rollout-plan.md",
        "docs/codex-agents.md",
        "docs/codex-skills.md",
    }

    # Patterns that indicate a runtime dependency on the in-repo mirror path.
    # We match the repo-relative path forms (with "./" or no path prefix),
    # NOT the user-scoped form ("~/.agents/skills" or "~/.codex/agents").
    # A literal "REPO_TARGET" constant is also prohibited.
    FORBIDDEN_PATTERNS = [
        # REPO_TARGET constant (definitional signal that repo mirroring is active)
        r'\bREPO_TARGET\b',
        # ./. agents/skills or ".agents/skills" without tilde prefix
        r'(?<!~/)(?<!\$HOME/)(?<!\$\{HOME\}/)(?<!home/)\.agents/skills',
        # .codex/agents without tilde prefix
        r'(?<!~/)(?<!\$HOME/)(?<!\$\{HOME\}/)(?<!home/)\.codex/agents',
    ]

    def _get_canonical_files(self) -> list[Path]:
        """Enumerate committed Python and shell scripts, excluding allowed files."""
        result = subprocess.run(
            ["git", "ls-files", "--", "scripts/", "core/", "tests/", ".github/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        files: list[Path] = []
        for line in result.stdout.splitlines():
            path = REPO_ROOT / line
            if any(line == allowed or line.endswith(f"/{allowed.lstrip('/')}") or Path(line).name == Path(allowed).name
                   for allowed in self.ALLOWED_FILES):
                continue
            if path.suffix in (".py", ".sh", ".yml", ".yaml") and path.is_file():
                files.append(path)
        return files

    def test_scripts_do_not_reference_repo_mirror_as_target(self) -> None:
        violations: list[str] = []
        for path in self._get_canonical_files():
            try:
                content = path.read_text(errors="replace")
            except OSError:
                continue
            rel = str(path.relative_to(REPO_ROOT))
            for pattern in self.FORBIDDEN_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    violations.append(f"{rel}: pattern '{pattern}' found ({len(matches)}x)")

        assert not violations, (
            "Canonical source files must not reference in-repo mirror paths as runtime targets.\n"
            "Violations:\n" + "\n".join(f"  - {v}" for v in violations)
        )


class TestSyncScriptsAreUserScopedOnly:
    """sync-codex-skills and sync-codex-agents must NOT define a REPO_TARGET constant."""

    def test_sync_codex_skills_has_no_repo_target(self) -> None:
        content = SYNC_SKILLS.read_text()
        assert "REPO_TARGET" not in content, (
            "scripts/sync-codex-skills must not define REPO_TARGET — "
            "user-scoped sync is the only mode."
        )

    def test_sync_codex_agents_has_no_repo_target(self) -> None:
        content = SYNC_AGENTS.read_text()
        assert "REPO_TARGET" not in content, (
            "scripts/sync-codex-agents must not define REPO_TARGET — "
            "user-scoped sync is the only mode."
        )

    def test_sync_codex_skills_has_user_target(self) -> None:
        content = SYNC_SKILLS.read_text()
        assert "user_target" in content or "USER_TARGET" in content, (
            "scripts/sync-codex-skills must define a user-scoped target path"
        )

    def test_sync_codex_agents_has_user_target(self) -> None:
        content = SYNC_AGENTS.read_text()
        assert "user_target" in content or "USER_TARGET" in content, (
            "scripts/sync-codex-agents must define a user-scoped target path"
        )


class TestArchitectureDocExists:
    """The principle must be documented explicitly."""

    def test_arch_doc_exists(self) -> None:
        assert ARCH_DOC.exists(), (
            f"docs/architecture/dev-repo-principle.md must exist at {ARCH_DOC}"
        )

    def test_arch_doc_declares_rm_rf_invariant(self) -> None:
        content = ARCH_DOC.read_text()
        # Must mention the rm -rf invariant
        assert "rm -rf" in content or "delete" in content.lower(), (
            "Architecture doc must declare the rm -rf invariant"
        )

    def test_arch_doc_mentions_user_scoped_targets(self) -> None:
        content = ARCH_DOC.read_text()
        assert "~/.codex" in content or "user-scoped" in content, (
            "Architecture doc must mention user-scoped targets"
        )

    def test_claude_md_references_arch_doc(self) -> None:
        claude_md = REPO_ROOT / "CLAUDE.md"
        content = claude_md.read_text()
        assert "dev-repo-principle" in content or "dev_repo_principle" in content, (
            "CLAUDE.md must reference docs/architecture/dev-repo-principle.md"
        )
