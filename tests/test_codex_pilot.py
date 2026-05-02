"""Tests for the full Codex skill export surface."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent
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


@pytest.fixture(scope="module")
def isolated_user_codex_skills(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, str]]:
    """Sync skills into an isolated HOME so tests do not depend on ~/.codex state."""
    home = tmp_path_factory.mktemp("codex-skills-home")
    user_codex_skills = home / ".codex" / "skills"
    user_codex_skills.mkdir(parents=True)
    env = {**os.environ, "HOME": str(home)}
    result = subprocess.run(
        [str(SYNC_SCRIPT)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"isolated skill sync failed:\n{result.stdout}{result.stderr}"
    return user_codex_skills, env


class TestInventorySurface:
    """Every exportable skill is discoverable by the inventory script.

    This repo is dev-only. The sync target is ~/.codex/skills (or ~/.agents/skills).
    In-repo mirrors (.agents/skills/) no longer exist. See TestUserScopedSync for runtime checks.
    See docs/architecture/dev-repo-principle.md.
    """

    def test_inventory_is_nonempty(self):
        assert INVENTORY, "codex_skills.py should discover exportable skills"

    def test_pilot_skills_are_still_discoverable(self):
        assert PILOT_SKILLS.issubset(SKILL_NAMES)

    def test_generated_metadata_skill_list_nonempty(self):
        assert GENERATED_METADATA_SKILLS, "Expected at least one generated metadata skill"


class TestUserScopedSync:
    """The user-scoped Codex skills sync target contains the full skill fleet.

    This repo is dev-only. The only sync target is ~/.codex/skills (or ~/.agents/skills).
    See docs/architecture/dev-repo-principle.md.
    """

    def test_every_discovered_skill_is_in_user_codex_skills(
        self, isolated_user_codex_skills: tuple[Path, dict[str, str]]
    ):
        user_codex_skills, _env = isolated_user_codex_skills
        missing = [skill for skill in SKILL_NAMES if not (user_codex_skills / skill).is_dir()]
        assert not missing, (
            f"Missing user-scoped skills: {missing}\nRun: scripts/sync-codex-skills"
        )

    def test_user_scoped_skills_have_skill_md(
        self, isolated_user_codex_skills: tuple[Path, dict[str, str]]
    ):
        user_codex_skills, _env = isolated_user_codex_skills
        missing = [
            skill for skill in SKILL_NAMES if not (user_codex_skills / skill / "SKILL.md").exists()
        ]
        assert not missing, f"Missing SKILL.md in user-scoped skills: {missing}"

    def test_user_scoped_skills_have_openai_yaml(
        self, isolated_user_codex_skills: tuple[Path, dict[str, str]]
    ):
        user_codex_skills, _env = isolated_user_codex_skills
        missing = [
            skill
            for skill in SKILL_NAMES
            if not (user_codex_skills / skill / "agents" / "openai.yaml").exists()
        ]
        assert not missing, f"Missing openai.yaml in user-scoped skills: {missing}"

    def test_generated_metadata_covers_non_pilot_skills(
        self, isolated_user_codex_skills: tuple[Path, dict[str, str]]
    ):
        user_codex_skills, _env = isolated_user_codex_skills
        for skill in GENERATED_METADATA_SKILLS[:5]:
            yaml_path = user_codex_skills / skill / "agents" / "openai.yaml"
            if not yaml_path.exists():
                continue  # Covered by test_user_scoped_skills_have_openai_yaml
            content = yaml_path.read_text()
            assert "display_name:" in content
            assert "short_description:" in content
            assert "default_prompt:" in content

    def test_full_fleet_user_sync_check_passes(
        self, isolated_user_codex_skills: tuple[Path, dict[str, str]]
    ):
        _user_codex_skills, env = isolated_user_codex_skills
        result = subprocess.run(
            [str(SYNC_SCRIPT), "--check"],
            cwd=REPO_ROOT,
            env=env,
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
