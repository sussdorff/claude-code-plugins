"""Tests for the skill-auditor Codex compatibility scanner."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent
SCAN_SCRIPT = REPO_ROOT / "meta" / "skills" / "skill-auditor" / "scripts" / "scan-codex-compat.py"


def scan_subset(*skills: str) -> list[dict[str, object]]:
    result = subprocess.run(
        [sys.executable, str(SCAN_SCRIPT), "--json", "--skills", ",".join(skills)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def test_portable_skill_scans_as_works_as_is() -> None:
    results = scan_subset("project-context")
    assert results[0]["status"] == "works-as-is"


def test_claude_specific_skill_scans_as_needs_fix() -> None:
    results = scan_subset("beads")
    assert results[0]["status"] == "needs-fix"
    findings = results[0]["findings"]
    assert findings, "needs-fix result must include findings"
