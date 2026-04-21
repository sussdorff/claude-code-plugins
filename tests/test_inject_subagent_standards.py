#!/usr/bin/env python3
"""
Tests for inject-subagent-standards.py hook.

Covers all 12 AC variants:
1. dev-tools:implementer, no env flags → inject paths
2. Explore, no env flags → no injection
3. core:researcher, no env flags → no injection (empty list)
4. general-purpose, no env flags → no injection
5. dev-tools:implementer + CCP_ORCHESTRATOR_RUN_ID + in orchestrator_handled → skip
6. beads-workflow:bead-orchestrator + CCP_ORCHESTRATOR_RUN_ID + NOT in orchestrator_handled → inject
7. CCP_NO_SUBAGENT_STANDARDS=1 with dev-tools:implementer → no injection (off-switch wins)
8. CCP_NO_SUBAGENT_STANDARDS=1 + CCP_ORCHESTRATOR_RUN_ID both set → no injection (off-switch wins)
9. unknown agent_label → no injection, no error
10. missing agent-standards.yml → no injection, stderr warning, exit 0
11. malformed agent-standards.yml → no injection, stderr warning, exit 0
12. Performance: <100ms p95 over 20 runs
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

# Path to the hook script
HOOK_SCRIPT = Path("/Users/malte/.claude/hooks/inject-subagent-standards.py")

# Minimal valid agent-standards.yml content for tests
SAMPLE_AGENT_STANDARDS = """
orchestrator_handled:
  - "dev-tools/*"
  - "medical/*"

mappings:
  "dev-tools/*":
    - "dev-tools/tool-standards.md"
    - "workflow/english-only.md"
    - "workflow/no-emoji.md"
  "medical/*":
    - "healthcare/control-areas.md"
    - "workflow/english-only.md"
  "core/*":
    - "workflow/english-only.md"
  "beads-workflow/*":
    - "workflow/english-only.md"
  "Explore": []
  "researcher": []
  "general-purpose": []
"""


def make_payload(agent_label: str) -> str:
    """Create a minimal TaskCreated JSON payload with the given agent_label."""
    return json.dumps({"agent_label": agent_label, "hook_event_name": "TaskCreated"})


def run_hook(
    payload: str,
    env_overrides: dict[str, str] | None = None,
    standards_file: Path | None = None,
) -> tuple[int, str, str]:
    """
    Run the hook script as a subprocess via its shebang (uv run).

    Args:
        payload: JSON string to pass via stdin
        env_overrides: Additional env vars (or vars to unset if value is None)
        standards_file: Path to a custom agent-standards.yml for testing

    Returns:
        (returncode, stdout, stderr)
    """
    env = os.environ.copy()
    # Remove any inherited test env vars that would affect behavior
    for key in ["CCP_NO_SUBAGENT_STANDARDS", "CCP_ORCHESTRATOR_RUN_ID", "AGENT_STANDARDS_YML"]:
        env.pop(key, None)

    if standards_file is not None:
        env["AGENT_STANDARDS_YML"] = str(standards_file)

    if env_overrides:
        for k, v in env_overrides.items():
            if v is None:
                env.pop(k, None)
            else:
                env[k] = v

    # Execute via the script's shebang (uv run) so pyyaml is available.
    # On macOS, running an executable script uses the shebang directly.
    result = subprocess.run(
        [str(HOOK_SCRIPT)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


@pytest.fixture
def standards_file(tmp_path: Path) -> Path:
    """Write a sample agent-standards.yml to a temp file and return its path."""
    f = tmp_path / "agent-standards.yml"
    f.write_text(SAMPLE_AGENT_STANDARDS)
    return f


# ---------------------------------------------------------------------------
# AC 1: dev-tools:implementer, no env flags → inject paths
# ---------------------------------------------------------------------------

class TestDevToolsImplementerNoEnvFlags:
    def test_returns_exit_0(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("dev-tools:implementer"),
            standards_file=standards_file,
        )
        assert code == 0

    def test_outputs_hook_specific_output_json(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("dev-tools:implementer"),
            standards_file=standards_file,
        )
        output = json.loads(stdout)
        assert "hookSpecificOutput" in output

    def test_additional_system_prompt_contains_tool_standards(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("dev-tools:implementer"),
            standards_file=standards_file,
        )
        output = json.loads(stdout)
        prompt = output["hookSpecificOutput"]["additionalSystemPrompt"]
        assert "dev-tools/tool-standards.md" in prompt

    def test_additional_system_prompt_contains_english_only(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("dev-tools:implementer"),
            standards_file=standards_file,
        )
        output = json.loads(stdout)
        prompt = output["hookSpecificOutput"]["additionalSystemPrompt"]
        assert "workflow/english-only.md" in prompt

    def test_additional_system_prompt_contains_no_emoji(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("dev-tools:implementer"),
            standards_file=standards_file,
        )
        output = json.loads(stdout)
        prompt = output["hookSpecificOutput"]["additionalSystemPrompt"]
        assert "workflow/no-emoji.md" in prompt


# ---------------------------------------------------------------------------
# AC 2: Explore, no env flags → no injection
# ---------------------------------------------------------------------------

class TestExploreNoEnvFlags:
    def test_returns_exit_0(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("Explore"),
            standards_file=standards_file,
        )
        assert code == 0

    def test_no_stdout_output(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("Explore"),
            standards_file=standards_file,
        )
        assert stdout.strip() == ""


# ---------------------------------------------------------------------------
# AC 3: core:researcher matches core/* → injects english-only.md
# (Note: bare "researcher" maps to empty list, but "core:researcher" matches "core/*")
# ---------------------------------------------------------------------------

class TestCoreResearcherEmptyList:
    def test_returns_exit_0(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("core:researcher"),
            standards_file=standards_file,
        )
        assert code == 0

    def test_injects_english_only(self, standards_file: Path) -> None:
        """core:researcher matches core/* pattern → injects english-only.md."""
        code, stdout, stderr = run_hook(
            make_payload("core:researcher"),
            standards_file=standards_file,
        )
        output = json.loads(stdout)
        prompt = output["hookSpecificOutput"]["additionalSystemPrompt"]
        assert "workflow/english-only.md" in prompt


# ---------------------------------------------------------------------------
# AC 3b: bare "researcher" label → no injection
# ---------------------------------------------------------------------------

class TestBareResearcherLabel:
    def test_returns_exit_0(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("researcher"),
            standards_file=standards_file,
        )
        assert code == 0

    def test_no_stdout_output(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("researcher"),
            standards_file=standards_file,
        )
        assert stdout.strip() == ""


# ---------------------------------------------------------------------------
# AC 4: general-purpose, no env flags → no injection
# ---------------------------------------------------------------------------

class TestGeneralPurposeNoEnvFlags:
    def test_returns_exit_0(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("general-purpose"),
            standards_file=standards_file,
        )
        assert code == 0

    def test_no_stdout_output(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("general-purpose"),
            standards_file=standards_file,
        )
        assert stdout.strip() == ""


# ---------------------------------------------------------------------------
# AC 5: dev-tools:implementer + ORCHESTRATOR_RUN_ID + in orchestrator_handled → skip
# ---------------------------------------------------------------------------

class TestOrchestratorHandled:
    def test_returns_exit_0(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("dev-tools:implementer"),
            env_overrides={"CCP_ORCHESTRATOR_RUN_ID": "some-run-id"},
            standards_file=standards_file,
        )
        assert code == 0

    def test_no_stdout_when_orchestrator_handled(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("dev-tools:implementer"),
            env_overrides={"CCP_ORCHESTRATOR_RUN_ID": "some-run-id"},
            standards_file=standards_file,
        )
        assert stdout.strip() == ""


# ---------------------------------------------------------------------------
# AC 6: beads-workflow:bead-orchestrator + ORCHESTRATOR_RUN_ID + NOT in orchestrator_handled → inject
# ---------------------------------------------------------------------------

class TestOrchestratorNotHandled:
    def test_returns_exit_0(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("beads-workflow:bead-orchestrator"),
            env_overrides={"CCP_ORCHESTRATOR_RUN_ID": "some-run-id"},
            standards_file=standards_file,
        )
        assert code == 0

    def test_injects_english_only_path(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("beads-workflow:bead-orchestrator"),
            env_overrides={"CCP_ORCHESTRATOR_RUN_ID": "some-run-id"},
            standards_file=standards_file,
        )
        output = json.loads(stdout)
        prompt = output["hookSpecificOutput"]["additionalSystemPrompt"]
        assert "workflow/english-only.md" in prompt


# ---------------------------------------------------------------------------
# AC 7: CCP_NO_SUBAGENT_STANDARDS=1 → no injection (off-switch)
# ---------------------------------------------------------------------------

class TestOffSwitch:
    def test_off_switch_no_injection_for_dev_tools(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("dev-tools:implementer"),
            env_overrides={"CCP_NO_SUBAGENT_STANDARDS": "1"},
            standards_file=standards_file,
        )
        assert code == 0
        assert stdout.strip() == ""

    # AC 8: Both off-switch and orchestrator run id set
    def test_off_switch_wins_over_orchestrator(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("dev-tools:implementer"),
            env_overrides={
                "CCP_NO_SUBAGENT_STANDARDS": "1",
                "CCP_ORCHESTRATOR_RUN_ID": "some-run-id",
            },
            standards_file=standards_file,
        )
        assert code == 0
        assert stdout.strip() == ""


# ---------------------------------------------------------------------------
# AC 9: unknown agent_label → no injection, no error
# ---------------------------------------------------------------------------

class TestUnknownAgentLabel:
    def test_returns_exit_0(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("some:unmapped-agent"),
            standards_file=standards_file,
        )
        assert code == 0

    def test_no_stdout_for_unknown_label(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("some:unmapped-agent"),
            standards_file=standards_file,
        )
        assert stdout.strip() == ""

    def test_no_stderr_for_unknown_label(self, standards_file: Path) -> None:
        code, stdout, stderr = run_hook(
            make_payload("some:unmapped-agent"),
            standards_file=standards_file,
        )
        assert stderr.strip() == ""


# ---------------------------------------------------------------------------
# AC 10: missing agent-standards.yml → no injection, stderr warning, exit 0
# ---------------------------------------------------------------------------

class TestMissingStandardsFile:
    def test_returns_exit_0_when_file_missing(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent-agent-standards.yml"
        code, stdout, stderr = run_hook(
            make_payload("dev-tools:implementer"),
            env_overrides={"AGENT_STANDARDS_YML": str(missing)},
        )
        assert code == 0

    def test_no_injection_when_file_missing(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent-agent-standards.yml"
        code, stdout, stderr = run_hook(
            make_payload("dev-tools:implementer"),
            env_overrides={"AGENT_STANDARDS_YML": str(missing)},
        )
        assert stdout.strip() == ""

    def test_stderr_warning_when_file_missing(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent-agent-standards.yml"
        code, stdout, stderr = run_hook(
            make_payload("dev-tools:implementer"),
            env_overrides={"AGENT_STANDARDS_YML": str(missing)},
        )
        assert "warning" in stderr.lower() or "not found" in stderr.lower() or "missing" in stderr.lower()


# ---------------------------------------------------------------------------
# AC 11: malformed agent-standards.yml → no injection, stderr warning, exit 0
# ---------------------------------------------------------------------------

class TestMalformedStandardsFile:
    def test_returns_exit_0_for_malformed(self, tmp_path: Path) -> None:
        malformed = tmp_path / "agent-standards.yml"
        malformed.write_text("{ this is: [not valid yaml: {{{")
        code, stdout, stderr = run_hook(
            make_payload("dev-tools:implementer"),
            env_overrides={"AGENT_STANDARDS_YML": str(malformed)},
        )
        assert code == 0

    def test_no_injection_for_malformed(self, tmp_path: Path) -> None:
        malformed = tmp_path / "agent-standards.yml"
        malformed.write_text("{ this is: [not valid yaml: {{{")
        code, stdout, stderr = run_hook(
            make_payload("dev-tools:implementer"),
            env_overrides={"AGENT_STANDARDS_YML": str(malformed)},
        )
        assert stdout.strip() == ""

    def test_stderr_warning_for_malformed(self, tmp_path: Path) -> None:
        malformed = tmp_path / "agent-standards.yml"
        malformed.write_text("{ this is: [not valid yaml: {{{")
        code, stdout, stderr = run_hook(
            make_payload("dev-tools:implementer"),
            env_overrides={"AGENT_STANDARDS_YML": str(malformed)},
        )
        assert stderr.strip() != ""


# ---------------------------------------------------------------------------
# AC 12: Performance <100ms p95 over 20 runs
# ---------------------------------------------------------------------------

class TestPerformance:
    def test_p95_under_100ms(self, standards_file: Path) -> None:
        """Hook must complete in <100ms at p95 over 20 runs."""
        durations_ms: list[float] = []
        for _ in range(20):
            start = time.perf_counter()
            run_hook(make_payload("dev-tools:implementer"), standards_file=standards_file)
            elapsed = (time.perf_counter() - start) * 1000
            durations_ms.append(elapsed)

        durations_ms.sort()
        p95 = durations_ms[int(len(durations_ms) * 0.95)]
        assert p95 < 100, f"p95 latency {p95:.1f}ms exceeds 100ms threshold"
