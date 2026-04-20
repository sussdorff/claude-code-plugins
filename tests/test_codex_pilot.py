"""
Test: CCP-c2p — Codex pilot skill surface.
Verifies that the 3 pilot skills are present and Codex-ready in .agents/skills/,
synced to the user-scoped Codex skills dir, have openai.yaml metadata, and that
the rollout plan has a locked Decisions section.
"""
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SKILL_NAMES = ["project-context", "spec-developer", "bug-triage"]
AGENTS_SKILLS = REPO_ROOT / ".agents" / "skills"
DEV_TOOLS_SKILLS = REPO_ROOT / "dev-tools" / "skills"
USER_CODEX_SKILLS = Path.home() / ".codex" / "skills"


class TestAgentsSkillsSurface:
    """AC#1: .agents/skills/ exists with 3 skills in Codex-usable form."""

    def test_agents_skills_dir_exists(self):
        assert AGENTS_SKILLS.is_dir(), ".agents/skills/ must exist"

    @pytest.mark.parametrize("skill", SKILL_NAMES)
    def test_skill_directory_exists(self, skill):
        assert (AGENTS_SKILLS / skill).is_dir()

    @pytest.mark.parametrize("skill", SKILL_NAMES)
    def test_skill_has_skill_md(self, skill):
        skill_md = AGENTS_SKILLS / skill / "SKILL.md"
        assert skill_md.exists(), f"{skill}/SKILL.md must exist"

    @pytest.mark.parametrize("skill", SKILL_NAMES)
    def test_skill_md_has_name_and_description(self, skill):
        skill_md = (AGENTS_SKILLS / skill / "SKILL.md").read_text()
        assert "name:" in skill_md
        assert "description:" in skill_md

    @pytest.mark.parametrize("skill", SKILL_NAMES)
    def test_agents_skills_in_sync_with_dev_tools(self, skill):
        """Run sync --check to verify .agents/skills matches dev-tools/skills."""
        import subprocess
        result = subprocess.run(
            ["scripts/sync-codex-skills", "--check", "--skills", skill],
            cwd=REPO_ROOT,
            capture_output=True, text=True
        )
        assert result.returncode == 0, (
            f"Skill {skill} is out of sync: {result.stdout}{result.stderr}\n"
            "Run: scripts/sync-codex-skills"
        )


class TestCodexMetadata:
    """AC#1: openai.yaml metadata present for each skill."""

    @pytest.mark.parametrize("skill", SKILL_NAMES)
    def test_openai_yaml_in_dev_tools(self, skill):
        yaml_path = DEV_TOOLS_SKILLS / skill / "agents" / "openai.yaml"
        assert yaml_path.exists(), f"dev-tools/skills/{skill}/agents/openai.yaml must exist"

    @pytest.mark.parametrize("skill", SKILL_NAMES)
    def test_openai_yaml_has_required_fields(self, skill):
        import yaml
        yaml_path = DEV_TOOLS_SKILLS / skill / "agents" / "openai.yaml"
        content = yaml.safe_load(yaml_path.read_text())
        iface = content.get("interface", {})
        assert "display_name" in iface, "openai.yaml must have interface.display_name"
        assert "short_description" in iface, "openai.yaml must have interface.short_description"
        assert "default_prompt" in iface, "openai.yaml must have interface.default_prompt"


class TestUserScopedSync:
    """AC#1/AC#2 precondition: skills synced to ~/.codex/skills/."""

    @pytest.mark.parametrize("skill", SKILL_NAMES)
    def test_skill_in_user_codex_skills(self, skill):
        skill_dir = USER_CODEX_SKILLS / skill
        assert skill_dir.is_dir(), (
            f"~/.codex/skills/{skill}/ must exist. "
            "Run: scripts/sync-codex-skills --user"
        )

    @pytest.mark.parametrize("skill", SKILL_NAMES)
    def test_user_skill_has_skill_md(self, skill):
        skill_md = USER_CODEX_SKILLS / skill / "SKILL.md"
        assert skill_md.exists()


class TestPilotEvidence:
    """AC#2: invocation transcripts exist."""

    def test_evidence_doc_exists(self):
        assert (REPO_ROOT / "docs" / "codex-pilot-evidence.md").exists()

    def test_evidence_has_three_skill_entries(self):
        content = (REPO_ROOT / "docs" / "codex-pilot-evidence.md").read_text()
        for skill in SKILL_NAMES:
            assert skill in content.lower(), f"Evidence must include {skill} transcript"

    def test_evidence_has_negative_check(self):
        content = (REPO_ROOT / "docs" / "codex-pilot-evidence.md").read_text()
        assert "negative" in content.lower() or "unrelated" in content.lower()


class TestRolloutPlanDecisions:
    """AC#4: Decisions section locked in rollout plan."""

    def test_decisions_section_exists(self):
        plan = (REPO_ROOT / "docs" / "codex-skills-rollout-plan.md").read_text()
        assert "## Decisions" in plan or "## Entscheidungen" in plan, (
            "Rollout plan must have a ## Decisions section"
        )

    def test_decisions_covers_source_of_truth(self):
        plan = (REPO_ROOT / "docs" / "codex-skills-rollout-plan.md").read_text()
        assert "source" in plan.lower() or "truth" in plan.lower() or "source of truth" in plan.lower()

    def test_decisions_covers_sync_mechanism(self):
        plan = (REPO_ROOT / "docs" / "codex-skills-rollout-plan.md").read_text()
        assert "sync" in plan.lower()

    def test_decisions_covers_metadata_depth(self):
        plan = (REPO_ROOT / "docs" / "codex-skills-rollout-plan.md").read_text()
        assert "metadata" in plan.lower() or "openai.yaml" in plan.lower()
