"""Tests for the full Codex skill export surface."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent
AGENTS_SKILLS = REPO_ROOT / ".agents" / "skills"
USER_CODEX_SKILLS = Path.home() / ".codex" / "skills"
INVENTORY_SCRIPT = REPO_ROOT / "scripts" / "codex_skills.py"
SYNC_SCRIPT = REPO_ROOT / "scripts" / "sync-codex-skills"
PILOT_SKILLS = {"project-context", "spec-developer", "bug-triage"}


def load_inventory() -> list[dict[str, object]]:
    result = subprocess.run(
        [sys.executable, str(INVENTORY_SCRIPT), "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


INVENTORY = load_inventory()
SKILL_NAMES = [record["name"] for record in INVENTORY]
GENERATED_METADATA_SKILLS = [
    record["name"] for record in INVENTORY if not bool(record["has_openai_yaml"])
]
_user_skills_present = USER_CODEX_SKILLS.is_dir()


class TestAgentsSkillsSurface:
    """Every exportable skill is present in the Codex-facing repo layer."""

    def test_inventory_is_nonempty(self):
        assert INVENTORY, "codex_skills.py should discover exportable skills"

    def test_pilot_skills_are_still_discoverable(self):
        assert PILOT_SKILLS.issubset(SKILL_NAMES)

    def test_agents_skills_dir_exists(self):
        assert AGENTS_SKILLS.is_dir(), ".agents/skills/ must exist"

    def test_every_discovered_skill_is_exported(self):
        missing = [skill for skill in SKILL_NAMES if not (AGENTS_SKILLS / skill).is_dir()]
        assert not missing, f"Missing exported skills: {missing}"

    def test_every_exported_skill_has_skill_md(self):
        missing = [
            skill for skill in SKILL_NAMES if not (AGENTS_SKILLS / skill / "SKILL.md").exists()
        ]
        assert not missing, f"Missing SKILL.md in exported skills: {missing}"

    def test_every_exported_skill_has_openai_yaml(self):
        missing = [
            skill
            for skill in SKILL_NAMES
            if not (AGENTS_SKILLS / skill / "agents" / "openai.yaml").exists()
        ]
        assert not missing, f"Missing openai.yaml in exported skills: {missing}"

    def test_generated_metadata_covers_non_pilot_skills(self):
        assert GENERATED_METADATA_SKILLS, "Expected at least one generated metadata skill"
        for skill in GENERATED_METADATA_SKILLS[:5]:
            yaml_path = AGENTS_SKILLS / skill / "agents" / "openai.yaml"
            content = yaml_path.read_text()
            assert "display_name:" in content
            assert "short_description:" in content
            assert "default_prompt:" in content

    def test_full_fleet_repo_sync_check_passes(self):
        result = subprocess.run(
            [str(SYNC_SCRIPT), "--check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (
            f"Full-fleet repo sync is out of date:\n{result.stdout}{result.stderr}"
        )


@pytest.mark.skipif(
    not _user_skills_present and not os.environ.get("PILOT_USER_SYNC"),
    reason="user-scoped sync not available on this machine (run sync-codex-skills --user or set PILOT_USER_SYNC=1)",
)
class TestUserScopedSync:
    """The user-scoped Codex skills dir mirrors the repo export for the full fleet."""

    def test_every_discovered_skill_is_in_user_codex_skills(self):
        missing = [skill for skill in SKILL_NAMES if not (USER_CODEX_SKILLS / skill).is_dir()]
        assert not missing, (
            f"Missing user-scoped skills: {missing}\nRun: scripts/sync-codex-skills --user"
        )

    def test_full_fleet_user_sync_check_passes(self):
        result = subprocess.run(
            [str(SYNC_SCRIPT), "--check", "--user"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (
            f"Full-fleet user sync is out of date:\n{result.stdout}{result.stderr}"
        )


class TestPilotEvidence:
    """AC#2: invocation transcripts exist."""

    def test_evidence_doc_exists(self):
        assert (REPO_ROOT / "docs" / "codex-pilot-evidence.md").exists()

    def test_evidence_has_three_skill_entries(self):
        content = (REPO_ROOT / "docs" / "codex-pilot-evidence.md").read_text()
        for skill in PILOT_SKILLS:
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
