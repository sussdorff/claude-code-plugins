#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pytest>=8.0",
#   "tomli>=2.0; python_version < '3.11'"
# ]
# ///
"""
Test: CCP-9yd — Codex session-close agent TOML structure.
Verifies that the Codex session-close agent TOML file exists, is parseable,
and contains all required sections for a complete session-close workflow.
"""
import sys
from pathlib import Path

import pytest

# Python 3.11+ has tomllib in stdlib; older versions need tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

REPO_ROOT = Path(__file__).parent.parent
PERSONAL_AGENT = Path.home() / ".codex" / "agents" / "session-close.toml"
PROJECT_AGENT = REPO_ROOT / ".codex" / "agents" / "session-close.toml"


class TestAgentFileExists:
    """AC1: Agent file exists at Codex discovery path."""

    def test_personal_agent_file_exists(self):
        assert PERSONAL_AGENT.exists(), (
            f"~/.codex/agents/session-close.toml must exist at {PERSONAL_AGENT}"
        )

    def test_project_agent_file_exists(self):
        assert PROJECT_AGENT.exists(), (
            f".codex/agents/session-close.toml must exist in repo at {PROJECT_AGENT}"
        )


class TestAgentTomlParseable:
    """AC1: Agent file is valid TOML."""

    def test_personal_agent_is_valid_toml(self):
        content = PERSONAL_AGENT.read_bytes()
        data = tomllib.loads(content.decode())
        assert isinstance(data, dict), "TOML must parse to a dict"

    def test_project_agent_is_valid_toml(self):
        content = PROJECT_AGENT.read_bytes()
        data = tomllib.loads(content.decode())
        assert isinstance(data, dict), "TOML must parse to a dict"


class TestAgentRequiredFields:
    """AC1+AC2: Required TOML fields and metadata present."""

    @pytest.fixture
    def agent_data(self):
        return tomllib.loads(PERSONAL_AGENT.read_bytes().decode())

    def test_developer_instructions_present(self, agent_data):
        assert "developer_instructions" in agent_data, (
            "developer_instructions is required in Codex agent TOML"
        )

    def test_developer_instructions_non_empty(self, agent_data):
        instructions = agent_data["developer_instructions"]
        assert isinstance(instructions, str)
        assert len(instructions.strip()) > 100, (
            "developer_instructions must be a non-trivial string"
        )

    def test_agent_section_present(self, agent_data):
        # name/description can be at top level or under [agent]
        has_name = "name" in agent_data or (
            "agent" in agent_data and "name" in agent_data.get("agent", {})
        )
        assert has_name, "Agent must have a name field"


class TestWorkflowSections:
    """AC2: All key workflow steps from the Claude version are reproduced."""

    @pytest.fixture
    def instructions(self):
        data = tomllib.loads(PERSONAL_AGENT.read_bytes().decode())
        return data["developer_instructions"].lower()

    def test_double_merge_strategy_present(self, instructions):
        assert "double-merge" in instructions or "double merge" in instructions, (
            "developer_instructions must document the double-merge strategy"
        )

    def test_step_1_present(self, instructions):
        assert "step 1" in instructions, (
            "developer_instructions must include Step 1 (setup & first merge)"
        )

    def test_changelog_section_present(self, instructions):
        assert "changelog" in instructions, (
            "developer_instructions must include changelog generation"
        )

    def test_bead_close_present(self, instructions):
        assert "bead" in instructions and "close" in instructions, (
            "developer_instructions must include bead close step"
        )

    def test_learnings_extraction_present(self, instructions):
        assert "learning" in instructions, (
            "developer_instructions must include learnings extraction"
        )

    def test_session_summary_present(self, instructions):
        assert "session summary" in instructions or "session debrief" in instructions, (
            "developer_instructions must include session summary/debrief"
        )

    def test_merge_feature_to_main_present(self, instructions):
        assert "merge feature" in instructions or "feature.*main" in instructions or "feature → main" in instructions or "feature->main" in instructions, (
            "developer_instructions must include feature→main merge"
        )

    def test_version_tag_present(self, instructions):
        assert "calver" in instructions or "version tag" in instructions or "version bump" in instructions, (
            "developer_instructions must include CalVer/version tag step"
        )

    def test_dolt_sync_present(self, instructions):
        assert "dolt" in instructions, (
            "developer_instructions must include dolt sync"
        )

    def test_git_push_present(self, instructions):
        assert "git push" in instructions or "push" in instructions, (
            "developer_instructions must include git push"
        )


class TestGapDocumentation:
    """AC3: Tool/capability gaps between Claude and Codex are documented."""

    @pytest.fixture
    def instructions(self):
        data = tomllib.loads(PERSONAL_AGENT.read_bytes().decode())
        return data["developer_instructions"]

    def test_gap_section_exists(self, instructions):
        assert "Tool / Capability Gaps" in instructions or "tool / capability gaps" in instructions.lower(), (
            "developer_instructions must contain a 'Tool / Capability Gaps' section"
        )

    def test_sandbox_mode_mentioned(self, instructions):
        assert "sandbox_mode" in instructions or "sandbox" in instructions.lower(), (
            "Gap section must mention sandbox_mode vs Claude tools: allowlist"
        )

    def test_open_brain_mentioned(self, instructions):
        assert "open-brain" in instructions.lower() or "open_brain" in instructions.lower(), (
            "Gap section must mention open-brain MCP availability in Codex"
        )


class TestDriftTracking:
    """AC6: Drift tracking comment present in TOML file."""

    @pytest.fixture
    def raw_content(self):
        return PERSONAL_AGENT.read_text()

    def test_source_of_truth_comment_present(self, raw_content):
        assert "Source of truth" in raw_content or "source of truth" in raw_content.lower(), (
            "TOML file must have a source-of-truth comment for drift tracking"
        )

    def test_drift_tracking_comment_references_claude_agent(self, raw_content):
        assert "session-close.md" in raw_content, (
            "Drift tracking comment must reference the Claude source file session-close.md"
        )


class TestPortabilityCompliance:
    """AC5: Agent conforms to portability rules (no Claude-specific tool names in instructions)."""

    @pytest.fixture
    def instructions(self):
        data = tomllib.loads(PERSONAL_AGENT.read_bytes().decode())
        return data["developer_instructions"]

    def test_no_mcp_tool_names_in_instructions(self, instructions):
        assert "mcp__open-brain__" not in instructions, (
            "Portable instructions must not contain mcp__open-brain__ tool names"
        )

    def test_no_claude_home_paths(self, instructions):
        assert "~/.claude/" not in instructions, (
            "Portable instructions must not contain ~/.claude/ paths"
        )

    def test_no_slash_command_syntax(self, instructions):
        import re
        # Check for slash-commands like /session-close, /spec-developer etc.
        # But allow path-style references like ~/.codex/agents/
        slash_commands = re.findall(r'(?<![/\w])/[a-z][a-z0-9-]+(?:\s|$)', instructions)
        assert not slash_commands, (
            f"Portable instructions must not contain slash-command invocations: {slash_commands}"
        )
