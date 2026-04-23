#!/usr/bin/env python3
"""
wave_helpers.py — Shared helpers for wave-orchestrator scripts.

Imported by wave-completion.py and wave-status.py to avoid duplication.
"""

import re
import subprocess
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Surface idle detection patterns
# ---------------------------------------------------------------------------

_THINKING_RE = re.compile(
    r"Newspapering|Baking|Crunched|Churned|Thinking|[0-9]+m\s*[0-9]+s|[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]"
)
_PROMPT_RE = re.compile(r"^\s*(\$|❯|➜|%)\s*$")
_DEAD_SURFACE_RE = re.compile(
    r"invalid_params|not a terminal|Surface.*not found|no such surface",
    re.IGNORECASE,
)


def _surface_is_idle(screen_text: str) -> bool:
    """Return True if the surface looks idle (shell prompt, no active thinking)."""
    lines = [line for line in screen_text.splitlines() if line.strip()]
    if not lines:
        return False
    last_nonempty = lines[-1]
    if not _PROMPT_RE.match(last_nonempty):
        return False
    preceding = lines[-3:-1] if len(lines) >= 3 else lines[:-1]
    for line in preceding:
        if _THINKING_RE.search(line):
            return False
    return True


def _read_surface(surface: str, lines: int = 5, scrollback: bool = False, runner=None) -> str:
    """Read a cmux surface. Returns empty string on error.

    Args:
        surface: The cmux surface identifier.
        lines: Number of lines to read.
        scrollback: Whether to include scrollback buffer.
        runner: Optional callable with the same signature as subprocess.run.
                Defaults to subprocess.run. Inject a mock for testing.
    """
    if runner is None:
        runner = subprocess.run
    cmd = ["cmux", "read-screen", "--surface", surface]
    if scrollback:
        cmd.append("--scrollback")
    if lines:
        cmd += ["--lines", str(lines)]
    try:
        result = runner(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout + result.stderr
    except Exception:
        return ""


def _bd_status(bead_id: str, runner=None) -> str:
    """Get bd status for a bead. Returns 'unknown' on failure.

    Args:
        bead_id: The bead identifier.
        runner: Optional callable with the same signature as subprocess.run.
                Defaults to subprocess.run. Inject a mock for testing.
    """
    if runner is None:
        runner = subprocess.run
    try:
        result = runner(
            ["bd", "show", bead_id],
            capture_output=True,
            text=True,
            timeout=15,
        )
        m = re.search(r"\b(OPEN|CLOSED|IN_PROGRESS|BLOCKED)\b", result.stdout)
        if m:
            return m.group(1).lower()
    except Exception:
        pass
    return "unknown"


def _elapsed_minutes(dispatch_time: str) -> int:
    """Compute elapsed minutes from dispatch_time ISO string. Returns 0 on error."""
    try:
        dt = datetime.strptime(dispatch_time.rstrip("Z"), "%Y-%m-%dT%H:%M:%S")
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        delta = now - dt
        return int(delta.total_seconds() / 60)
    except Exception:
        return 0
