"""Tests for skill-auditor validate-skill.py — EXTRACTABLE_CODE enforcement in SKILL.md files."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path


VALIDATOR = Path("meta/skills/skill-auditor/scripts/validate-skill.py")


def write_skill(tmp_path: Path, body: str) -> Path:
    """Create a minimal valid SKILL.md with the given body."""
    skill_dir = tmp_path / "sample-skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        textwrap.dedent(
            f"""\
---
name: sample-skill
description: Does something useful when the user asks for it.
---

# Sample Skill

Handles sample tasks.

## When to Use

- "Do the sample thing"
- "Run sample workflow"

{body}
"""
        )
    )
    return skill_file


def run_validator(skill_path: Path, extra_args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(VALIDATOR), str(skill_path)]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def test_flags_large_bash_block_in_body(tmp_path: Path) -> None:
    """Shell block > 5 real lines in SKILL.md body → BLOCKING finding."""
    skill = write_skill(
        tmp_path,
        """
## Workflow

```bash
CONFIG=$(cat config.json)
WAVE_ID=$(echo "$CONFIG" | jq -r '.wave_id')
SURFACE=$(echo "$CONFIG" | jq -r '.surface')
SCREEN=$(cat screen.txt)
STATUS=$(echo "$SCREEN" | grep error)
DETAIL=$(echo "$SCREEN" | sed -n '1,5p')
echo "$STATUS"
```
""",
    )
    result = run_validator(skill)

    assert result.returncode == 1
    assert "EXTRACTABLE_CODE" in result.stdout
    assert "BLOCKING" in result.stdout


def test_flags_large_python_block_in_body(tmp_path: Path) -> None:
    """Python block > 3 real lines in SKILL.md body → BLOCKING finding."""
    skill = write_skill(
        tmp_path,
        """
## Processing

```python
import json
import sys
data = json.load(sys.stdin)
result = process(data)
print(json.dumps(result))
```
""",
    )
    result = run_validator(skill)

    assert result.returncode == 1
    assert "EXTRACTABLE_CODE" in result.stdout
    assert "BLOCKING" in result.stdout


def test_flags_pipeline_in_body(tmp_path: Path) -> None:
    """Shell block with 3+ pipeline markers → ADVISORY finding."""
    skill = write_skill(
        tmp_path,
        """
## Discovery

```bash
find ~/.claude -name "*.md" | grep skill | head -10
```
""",
    )
    result = run_validator(skill)

    # This is a short block with pipeline markers — should be ADVISORY not BLOCKING
    assert "EXTRACTABLE_CODE" in result.stdout
    assert "ADVISORY" in result.stdout


def test_flags_verbal_pipeline_in_body(tmp_path: Path) -> None:
    """Numbered ordered list with 4+ items containing tool keywords → ADVISORY finding."""
    skill = write_skill(
        tmp_path,
        """
## Steps

1. Run the scan script to search all skills for violations.
2. Parse the output and grep for BLOCKING findings.
3. Query the database to check if the skill was previously reviewed.
4. Call the auditor agent to check the result.
5. Store the final report in the workspace.
""",
    )
    result = run_validator(skill)

    assert "EXTRACTABLE_CODE" in result.stdout
    assert "ADVISORY" in result.stdout


def test_clean_skill_passes(tmp_path: Path) -> None:
    """Skill that only references $SCRIPT calls → exit 0, no EXTRACTABLE_CODE."""
    skill = write_skill(
        tmp_path,
        """
## Workflow

Run `$SCRIPT` to discover skills. The script outputs a JSON result per
`core/contracts/execution-result.schema.json`.

- Inspect `status` field for errors
- Check `data.skills` for the skill list
""",
    )
    result = run_validator(skill)

    assert result.returncode == 0
    assert "EXTRACTABLE_CODE" not in result.stdout


def test_single_command_snippet_passes(tmp_path: Path) -> None:
    """Single-command snippet (e.g. bd show <id>) should not be flagged."""
    skill = write_skill(
        tmp_path,
        """
## Quick Reference

Run `bd show <id>` to inspect a bead.

```bash
bd show CCP-123
```
""",
    )
    result = run_validator(skill)

    assert result.returncode == 0
    assert "EXTRACTABLE_CODE" not in result.stdout


def test_strict_mode_exits_nonzero_on_advisory(tmp_path: Path) -> None:
    """With --strict, an ADVISORY finding → exit 1."""
    skill = write_skill(
        tmp_path,
        """
## Discovery

```bash
find ~/.claude -name "*.md" | grep skill | head -10
```
""",
    )
    result = run_validator(skill, extra_args=["--strict"])

    assert result.returncode == 1
    assert "EXTRACTABLE_CODE" in result.stdout
    assert "ADVISORY" in result.stdout


def test_flags_cwd_relative_plugin_path(tmp_path: Path) -> None:
    """CWD-relative `beads-workflow/scripts/x.py` in a bash block → BLOCKING PLUGIN_PATH."""
    skill = write_skill(
        tmp_path,
        """
## Claim

```bash
python3 beads-workflow/scripts/claim-bead.py foo --bar
```
""",
    )
    result = run_validator(skill)

    assert result.returncode == 1, f"Expected exit 1, got {result.returncode}\nstdout:\n{result.stdout}"
    assert "PLUGIN_PATH" in result.stdout
    assert "BLOCKING" in result.stdout
    assert "beads-workflow/scripts/claim-bead.py" in result.stdout


def test_plugin_root_env_var_passes(tmp_path: Path) -> None:
    """`${CLAUDE_PLUGIN_ROOT}/scripts/x.py` → no PLUGIN_PATH finding."""
    skill = write_skill(
        tmp_path,
        """
## Claim

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/claim-bead.py" foo --bar
```
""",
    )
    result = run_validator(skill)

    assert "PLUGIN_PATH" not in result.stdout, f"Unexpected PLUGIN_PATH finding:\n{result.stdout}"


def test_absolute_plugin_path_passes(tmp_path: Path) -> None:
    """Absolute path containing `beads-workflow/scripts/…` (e.g. via plugins cache) is OK."""
    skill = write_skill(
        tmp_path,
        """
## Example

```bash
python3 /Users/me/.claude/plugins/cache/sussdorff-plugins/beads-workflow/scripts/claim-bead.py
```
""",
    )
    result = run_validator(skill)

    assert "PLUGIN_PATH" not in result.stdout


def test_plugin_path_in_non_shell_block_ignored(tmp_path: Path) -> None:
    """A plugin path mentioned in a markdown/text block is prose, not an exec — ignore."""
    skill = write_skill(
        tmp_path,
        """
## Reference

```markdown
See beads-workflow/scripts/claim-bead.py for the claim helper.
```
""",
    )
    result = run_validator(skill)

    # markdown fences are not bash/sh/zsh/python so PLUGIN_PATH must not fire.
    assert "PLUGIN_PATH" not in result.stdout


def test_plugin_path_all_known_folders(tmp_path: Path) -> None:
    """All known plugin folders trigger the check."""
    for folder in ("beads-workflow", "core", "dev-tools", "meta", "infra",
                   "business", "content", "medical", "open-brain"):
        subdir = tmp_path / folder.replace("/", "_")
        subdir.mkdir(exist_ok=True)
        skill = write_skill(
            subdir,
            f"""
## Run

```bash
python3 {folder}/scripts/something.py
```
""",
        )
        result = run_validator(skill)
        assert "PLUGIN_PATH" in result.stdout, (
            f"Expected PLUGIN_PATH flag for `{folder}/scripts/something.py`, got:\n{result.stdout}"
        )


def test_exit_1_on_blocking(tmp_path: Path) -> None:
    """BLOCKING finding → exit 1 regardless of --strict."""
    skill = write_skill(
        tmp_path,
        """
## Workflow

```bash
CONFIG=$(cat wave.json)
WAVE_ID=$(echo "$CONFIG" | jq -r '.wave_id')
SURFACE=$(echo "$CONFIG" | jq -r '.surface')
SCREEN=$(cat screen.txt)
STATUS=$(echo "$SCREEN" | grep -i error | tail -1)
DETAIL=$(echo "$SCREEN" | sed -n '1,20p')
echo "$STATUS"
```
""",
    )
    result = run_validator(skill)

    assert result.returncode == 1
    assert "EXTRACTABLE_CODE" in result.stdout
    assert "BLOCKING" in result.stdout
