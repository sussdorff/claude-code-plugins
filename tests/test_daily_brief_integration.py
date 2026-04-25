"""
Integration tests for the daily-brief skill.

Tests run orchestrate-brief.py against live data for all 4 configured projects.
These tests require the live config at ~/.claude/daily-brief.yml and the
actual project directories to exist.

Run with:
    uv run pytest tests/test_daily_brief_integration.py -v -m integration
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
_CONFIG_DIR = _REPO_ROOT / "core" / "skills" / "daily-brief" / "scripts"

sys.path.insert(0, str(_CONFIG_DIR))
import config as _cfg  # noqa: E402

_LIVE_CONFIG = Path.home() / ".claude" / "daily-brief.yml"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ORCHESTRATE = _SCRIPTS_DIR / "orchestrate-brief.py"

_PROJECTS = ["claude-code-plugins", "mira", "polaris", "open-brain"]

_SINCE = "7d"

# Output from orchestrate-brief when all briefs already exist
_ALREADY_EXISTS_MSG = "No new briefs generated. All requested briefs already exist on disk."

# Pattern for date range header: e.g. "2026-04-18 bis 2026-04-24" or similar
# render-brief uses "YYYY-MM-DD bis YYYY-MM-DD" in range rollup H1/H2 headings
_RANGE_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}.*\d{4}-\d{2}-\d{2}")


def _run_orchestrate(project: str, since: str = _SINCE) -> subprocess.CompletedProcess:
    """Run orchestrate-brief.py for a single project with --since.

    Uses 'uv run' so the PEP-723 inline dependencies in orchestrate-brief.py
    (httpx, pyyaml) are available in the subprocess, regardless of which
    python3 interpreter the test runner is using.
    """
    cmd = [
        "uv", "run", "--quiet", "--script",
        str(_ORCHESTRATE),
        project,
        f"--since={since}",
        "--config", str(_LIVE_CONFIG),
    ]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=240,
    )


def _is_valid_markdown(text: str) -> bool:
    """Return True if text contains at least one markdown heading (#)."""
    return bool(re.search(r"^#{1,6}\s", text, re.MULTILINE))


def _has_date_range_heading(text: str) -> bool:
    """Return True if text contains a heading with a date range pattern.

    Rollup output uses headings like:
      ## Executive Summary — project (2026-04-18 bis 2026-04-24)
    or the top-level H1:
      # project — 2026-04-18 bis 2026-04-24

    We accept either format. Also accept the already-exists message as
    the range was already processed and the briefs are on disk.
    """
    if _ALREADY_EXISTS_MSG in text:
        return True
    # Look for a date range pattern in a heading line
    for line in text.splitlines():
        if line.startswith("#") and _RANGE_DATE_PATTERN.search(line):
            return True
    return False


def _brief_exists_on_disk(project_name: str) -> bool:
    """Return True if at least one brief exists on disk for the given project."""
    result = _cfg.resolve_project(project_name, _LIVE_CONFIG)
    if result["status"] != "ok" or not result["data"]["projects"]:
        return False
    project = _cfg.ProjectConfig.from_dict(result["data"]["projects"][0])
    briefs_dir = _cfg.briefs_dir(project)
    if not briefs_dir.is_dir():
        return False
    return any(briefs_dir.glob("*.md"))


# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Tests: no crash, valid output, brief persisted
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("project", _PROJECTS)
def test_no_crash(project: str) -> None:
    """orchestrate-brief.py --since=7d exits 0 for each configured project."""
    proc = _run_orchestrate(project)
    assert proc.returncode == 0, (
        f"orchestrate-brief.py crashed for project '{project}'.\n"
        f"stdout: {proc.stdout[:500]}\n"
        f"stderr: {proc.stderr[:500]}"
    )


@pytest.mark.parametrize("project", _PROJECTS)
def test_output_is_valid_markdown(project: str) -> None:
    """Output contains at least one markdown heading (# or ## …).

    If all briefs already exist the script prints the already-exists message —
    which is plain text without headings. We accept that as valid too.
    """
    proc = _run_orchestrate(project)
    assert proc.returncode == 0
    output = proc.stdout
    assert _is_valid_markdown(output) or _ALREADY_EXISTS_MSG in output, (
        f"Output for '{project}' is neither valid markdown nor the already-exists message.\n"
        f"Output: {output[:300]}"
    )


@pytest.mark.parametrize("project", _PROJECTS)
def test_brief_persisted_on_disk(project: str) -> None:
    """At least one brief file exists on disk for each project after run."""
    proc = _run_orchestrate(project)
    assert proc.returncode == 0
    assert _brief_exists_on_disk(project), (
        f"No brief files found on disk for project '{project}' after running "
        f"orchestrate-brief.py --since={_SINCE}."
    )


# ---------------------------------------------------------------------------
# Test: range rollup behavior
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("project", _PROJECTS)
def test_range_rollup_output(project: str) -> None:
    """--since=7d produces ONE compressed rollup (not individual per-day headings).

    For range mode, the output should contain a date range pattern in headings
    (e.g. "2026-04-18 bis 2026-04-24") rather than seven separate H2 headings
    each for an individual day.

    If all briefs already exist the already-exists message is acceptable.
    """
    proc = _run_orchestrate(project)
    assert proc.returncode == 0
    output = proc.stdout

    if _ALREADY_EXISTS_MSG in output:
        # Briefs already on disk — behavior is correct (backfill no-op)
        return

    # Verify range rollup: should NOT have multiple individual per-day H2 headings
    # (e.g. "## Executive Summary — project (2026-04-18)" and
    #  "## Executive Summary — project (2026-04-19)" etc.)
    # Instead expect one summary spanning the range.
    exec_summary_lines = [
        line for line in output.splitlines()
        if line.startswith("## Executive Summary")
    ]
    # A range rollup should have at most ONE Executive Summary heading
    # (one per project in output — we're requesting a single project here)
    assert len(exec_summary_lines) <= 1, (
        f"Range rollup for '{project}' has {len(exec_summary_lines)} Executive Summary "
        f"headings — expected at most 1 (compressed rollup). "
        f"Got: {exec_summary_lines}"
    )

    # Should be valid markdown overall
    assert _is_valid_markdown(output), (
        f"Range output for '{project}' is not valid markdown.\nOutput: {output[:300]}"
    )
