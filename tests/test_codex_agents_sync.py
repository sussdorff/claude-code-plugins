"""Tests for the tracked Codex agent sync surfaces.

This repo is dev-only. The only sync target is ~/.codex/agents/.
In-repo mirrors (.codex/agents/) no longer exist.
See docs/architecture/dev-repo-principle.md.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent
SOURCE_DIR = REPO_ROOT / "dev-tools" / "codex-agents"
USER_CODEX_AGENTS = Path.home() / ".codex" / "agents"
INVENTORY_SCRIPT = REPO_ROOT / "scripts" / "codex_agents.py"
SYNC_SCRIPT = REPO_ROOT / "scripts" / "sync-codex-agents"


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
AGENT_NAMES = [record["name"] for record in INVENTORY]
_user_agents_present = USER_CODEX_AGENTS.is_dir()


class TestTrackedCodexAgents:
    """Every tracked agent source exists in dev-tools/codex-agents/."""

    def test_inventory_is_nonempty(self) -> None:
        assert INVENTORY, "codex_agents.py should discover tracked agents"

    def test_source_dir_exists(self) -> None:
        assert SOURCE_DIR.is_dir(), "dev-tools/codex-agents/ must exist"

    def test_every_discovered_agent_has_a_tracked_source(self) -> None:
        missing = [
            record["name"]
            for record in INVENTORY
            if not (REPO_ROOT / str(record["source_file"])).exists()
        ]
        assert not missing, f"Missing tracked agent sources: {missing}"


@pytest.mark.skipif(
    not _user_agents_present and not os.environ.get("CODEX_AGENT_USER_SYNC"),
    reason="user-scoped Codex agents not available on this machine (run sync-codex-agents or set CODEX_AGENT_USER_SYNC=1)",
)
class TestUserScopedCodexAgentSync:
    """The user-scoped Codex agent dir (~/.codex/agents/) contains the tracked fleet.

    This repo is dev-only. The only sync target is ~/.codex/agents/.
    See docs/architecture/dev-repo-principle.md.
    """

    def test_every_discovered_agent_is_in_user_codex_agents(self) -> None:
        missing = [name for name in AGENT_NAMES if not (USER_CODEX_AGENTS / f"{name}.toml").exists()]
        assert not missing, (
            f"Missing user-scoped Codex agents: {missing}\nRun: scripts/sync-codex-agents"
        )

    def test_user_sync_check_passes(self) -> None:
        result = subprocess.run(
            [str(SYNC_SCRIPT), "--check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (
            f"User-scoped Codex agents are out of date:\n{result.stdout}{result.stderr}"
        )
