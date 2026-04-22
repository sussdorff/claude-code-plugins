"""Tests for agent-forge validator warnings around embedded executable workflows."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path


VALIDATOR = Path("meta/skills/agent-forge/scripts/validate-agent.py")


def write_agent(tmp_path: Path, body: str) -> Path:
    agent = tmp_path / "sample-agent.md"
    agent.write_text(
        textwrap.dedent(
            f"""\
---
name: sample-agent
description: Reviews code when the user asks for an isolated review.
tools: Read, Grep, Glob
model: sonnet
---

# Purpose

Review the target carefully.

## Instructions

1. Read the target.
2. Analyze the important risks.
3. Report the result.

## Output Format

Return findings first.

## Pre-flight Checklist

- [ ] Confirm the target exists.

## Responsibility

Owns: review
Does NOT Own: edits

## VERIFY

```bash
rg --files
```

## LEARN

- Do not skip verification.

{body}
"""
        )
    )
    return agent


def run_validator(agent_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(agent_path)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_warns_on_large_shell_block(tmp_path: Path) -> None:
    agent = write_agent(
        tmp_path,
        """
        ```bash
        CONFIG=$(cat wave.json)
        WAVE_ID=$(echo "$CONFIG" | jq -r '.wave_id')
        SURFACE=$(echo "$CONFIG" | jq -r '.beads[0].surface')
        SCREEN=$(cmux read-screen --surface "$SURFACE" --scrollback --lines 60 2>&1 || true)
        STATUS=$(echo "$SCREEN" | grep -i error | tail -1)
        DETAIL=$(echo "$SCREEN" | sed -n '1,20p')
        FOLLOW_UP=$(bd show CCP-123 | grep -oE 'OPEN|CLOSED' | head -1)
        METRICS=$(sqlite3 ~/.claude/metrics.db "SELECT COUNT(*) FROM agent_calls;")
        echo "$WAVE_ID"
        echo "$STATUS"
        echo "$DETAIL"
        echo "$FOLLOW_UP"
        echo "$METRICS"
        ```
        """,
    )
    result = run_validator(agent)

    assert result.returncode == 0
    assert "Extractable executable code" in result.stdout
    assert "Inline multi-step shell pipeline detected" in result.stdout
    assert "execution-result.schema.json" in result.stdout


def test_warns_on_inline_python_c(tmp_path: Path) -> None:
    agent = write_agent(
        tmp_path,
        """
        Run this inline:

        ```bash
        uv run python -c "import json,sys; print(json.dumps({'status': 'ok'}))"
        ```
        """,
    )
    result = run_validator(agent)

    assert result.returncode == 0
    assert "Inline Python -c invocation detected in prompt" in result.stdout


def test_clean_prompt_has_no_extractable_code_warning(tmp_path: Path) -> None:
    agent = write_agent(
        tmp_path,
        """
        ## Script Boundaries

        - Use bundled scripts for deterministic workflows.
        - Keep this prompt focused on judgment and prioritization.
        """,
    )
    result = run_validator(agent)

    assert result.returncode == 0
    assert "Extractable executable code" not in result.stdout
    assert "Inline multi-step shell pipeline detected" not in result.stdout
    assert "Inline Python -c invocation detected in prompt" not in result.stdout
