#!/usr/bin/env python3
"""Stop hook: beads-workflow session-end safety net.

Fires when the main Claude Code session stops. Provides a safety net
for sessions that end without session-close having been run.

Behavior:
- Loop prevention: skips if stop_hook_active is true
- Only active inside a Claude Code worktree (.claude/worktrees/ in cwd)
- Extracts bead_id from path segment "bead-<id>"
- Dedup protection: no-op if bead is already "closed" (session-close ran)
- Safety-net: appends a note if bead is "in_progress" (session-close did NOT run)

Exit codes: always 0 (non-blocking, observability-only).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys

_WORKTREE_MARKER = ".claude/worktrees/"
_BEAD_SEGMENT_RE = re.compile(r"(?:^|/)bead-([A-Za-z0-9]+-[A-Za-z0-9.]+)(?:/|$)")  # Format: <PREFIX>-<SUFFIX>, e.g. CCP-o4z, open-brain-xyz, CCP-2vo.8
_SAFETY_NET_NOTE = (
    "Session ended without session-close. "
    "Run session-close manually to merge and push."
)


def extract_bead_id(cwd: str) -> str | None:
    """Extract bead ID from a Claude Code worktree path.

    Args:
        cwd: The working directory path to inspect.

    Returns:
        The bead ID string (e.g. "CCP-o4z") if found, otherwise None.
    """
    if _WORKTREE_MARKER not in cwd:
        return None
    m = _BEAD_SEGMENT_RE.search(cwd)
    return m.group(1) if m else None


def _get_bead_status(bead_id: str) -> str | None:
    """Fetch the bead status via `bd show <id> --json`.

    Args:
        bead_id: The bead identifier to query.

    Returns:
        The status string (e.g. "in_progress", "closed") or None on error.
    """
    try:
        result = subprocess.run(
            ["bd", "show", bead_id, "--json"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        if isinstance(data, list):
            data = data[0] if data else {}
        return data.get("status")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def _append_safety_note(bead_id: str) -> None:
    """Append a safety-net note to the bead using bd update.

    Args:
        bead_id: The bead identifier to update.
    """
    try:
        subprocess.run(
            ["bd", "update", bead_id, f"--append-notes={_SAFETY_NET_NOTE}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception as e:
        print(f"[session-end] error: {e}", file=sys.stderr)


def handle(payload: dict) -> None:
    """Process the Stop hook payload.

    Args:
        payload: Parsed JSON from stdin (Stop hook event).
    """
    # AK2: Loop prevention
    if payload.get("stop_hook_active"):
        return

    # AK3: Only active inside a worktree
    cwd = payload.get("cwd", "")
    bead_id = extract_bead_id(cwd)
    if bead_id is None:
        return

    # AK4: bead_id extracted — now query status
    status = _get_bead_status(bead_id)

    # AK6: Dedup — skip if closed (session-close already ran)
    if status == "closed":
        return

    # AK5: Safety net — append note when still in_progress
    if status == "in_progress":
        _append_safety_note(bead_id)
        print(
            f"[session-end] Safety net fired for bead {bead_id}: "
            f"session ended without session-close. Note appended.",
            file=sys.stderr,
        )


def main() -> None:
    """Stop hook entry point.

    Reads stdin JSON, calls handle(), always exits 0.
    """
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw)
    except (json.JSONDecodeError, EOFError, ValueError, OSError):
        payload = {}

    try:
        handle(payload)
    except Exception as e:
        print(f"[session-end] error: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
