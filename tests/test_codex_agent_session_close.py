#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pytest>=8.0"
# ]
# ///
"""
Tests for the Codex session-close agent TOML.
Validates structure, required fields, and key workflow sections (CCP-9yd).
"""

import tomllib
import pytest
import re
from pathlib import Path

PERSONAL_AGENT_PATH = Path.home() / ".codex" / "agents" / "session-close.toml"
REPO_AGENT_PATH = Path(__file__).parent.parent / ".codex" / "agents" / "session-close.toml"


def load_toml(path: Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


class TestAgentExists:
    def test_personal_agent_exists(self):
        assert PERSONAL_AGENT_PATH.exists(), f"Not found: {PERSONAL_AGENT_PATH}"

    def test_repo_agent_exists(self):
        assert REPO_AGENT_PATH.exists(), f"Not found: {REPO_AGENT_PATH}"

    def test_personal_and_repo_in_sync(self):
        assert PERSONAL_AGENT_PATH.read_text() == REPO_AGENT_PATH.read_text(), "Out of sync"


class TestAgentStructure:
    @pytest.fixture
    def agent(self):
        return load_toml(PERSONAL_AGENT_PATH)

    def test_toml_parseable(self, agent):
        assert isinstance(agent, dict)

    def test_has_developer_instructions(self, agent):
        assert "developer_instructions" in agent
        assert len(agent["developer_instructions"]) > 100

    def test_has_name(self, agent):
        assert agent.get("name") == "session-close"

    def test_has_sandbox_mode(self, agent):
        assert agent.get("sandbox_mode") == "workspace-write"

    def test_has_nickname_candidates(self, agent):
        assert len(agent.get("nickname_candidates", [])) >= 3


class TestWorkflowContent:
    @pytest.fixture
    def instructions(self):
        return load_toml(PERSONAL_AGENT_PATH)["developer_instructions"]

    def test_has_double_merge(self, instructions):
        assert "double-merge" in instructions.lower() or "Double-Merge" in instructions

    def test_has_step_references(self, instructions):
        assert "Step 1" in instructions

    def test_has_changelog(self, instructions):
        assert "changelog" in instructions.lower()

    def test_has_version_tag(self, instructions):
        assert "version" in instructions.lower()

    def test_has_bead_close(self, instructions):
        assert "bd close" in instructions

    def test_has_dolt_sync(self, instructions):
        assert "bd dolt" in instructions

    def test_has_learnings(self, instructions):
        assert "learning" in instructions.lower()

    def test_has_summary(self, instructions):
        assert "summary" in instructions.lower()

    def test_has_pipeline_watch(self, instructions):
        assert "pipeline" in instructions.lower()

    def test_has_open_brain_fallback(self, instructions):
        assert "fallback" in instructions.lower()


class TestGapDocumentation:
    @pytest.fixture
    def instructions(self):
        return load_toml(PERSONAL_AGENT_PATH)["developer_instructions"]

    def test_gap_section_exists(self, instructions):
        assert "Tool / Capability Gaps" in instructions

    def test_documents_subagent_gap(self, instructions):
        assert "subagent" in instructions.lower()

    def test_documents_sandbox_mode_gap(self, instructions):
        assert "sandbox_mode" in instructions

    def test_documents_open_brain(self, instructions):
        assert "open-brain" in instructions.lower()


class TestPortabilityCompliance:
    @pytest.fixture
    def instructions(self):
        return load_toml(PERSONAL_AGENT_PATH)["developer_instructions"]

    def test_no_mcp_tool_prefix(self, instructions):
        assert "mcp__" not in instructions

    def test_no_claude_home_paths(self, instructions):
        assert "~/.claude" not in instructions

    def test_no_slash_commands(self, instructions):
        matches = re.findall(r'(?<!\w)/[a-z][a-z-]+', instructions)
        path_like = [m for m in matches if any(x in m for x in ["/bin", "/usr", "/dev", "/etc"])]
        non_path = [m for m in matches if m not in path_like]
        assert not non_path, f"Slash-command syntax found: {non_path}"


class TestDriftTracking:
    def test_source_of_truth_comment(self):
        content = PERSONAL_AGENT_PATH.read_text()
        assert "Source of truth" in content

    def test_sync_date_comment(self):
        content = PERSONAL_AGENT_PATH.read_text()
        assert "Last synced" in content or "synced" in content.lower()
