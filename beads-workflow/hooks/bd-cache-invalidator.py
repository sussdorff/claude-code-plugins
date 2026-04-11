#!/usr/bin/env python3
"""Claude Code PostToolUse Bash hook: invalidate bead cache on mutating bd commands.

Reads stdin JSON (PostToolUse event), checks tool_input.command for bd create/close/update/delete
using word-boundary matching, and touches ~/.claude/state/beads-cache.dirty.

Must complete within 50ms.
Returns 0 always — never blocks tool execution.

Registration in ~/.claude/settings.json (PostToolUse hooks, matcher: "Bash"):
  {"type": "command",
   "command": "<claude-config-repo>/malte/hooks/bd-cache-invalidator.py"}
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_DEFAULT_DIRTY_FLAG = Path.home() / ".claude" / "state" / "beads-cache.dirty"
DIRTY_FLAG: Path = Path(os.environ.get("BEADS_DIRTY_FLAG") or str(_DEFAULT_DIRTY_FLAG))

# Word-boundary pattern: matches `bd create`, `bd close`, `bd update`, or `bd delete`
# as distinct words — not as substrings of longer identifiers.
_MUTATING_PATTERN = re.compile(r"\bbd (create|close|update|delete)\b")


def maybe_set_dirty(command: str) -> None:
    """Touch the dirty flag if command is a mutating bd operation.

    Args:
        command: The bash command string from tool_input.command.
    """
    if not _MUTATING_PATTERN.search(command):
        return
    try:
        DIRTY_FLAG.parent.mkdir(parents=True, exist_ok=True)
        DIRTY_FLAG.touch()
    except OSError:
        pass  # Fail silently — never block tool execution


def main() -> None:
    """PostToolUse hook entry point.

    Reads stdin JSON, extracts command, conditionally sets dirty flag.
    Never raises, always exits 0.
    """
    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError, ValueError, OSError):
        return

    try:
        command = event.get("tool_input", {}).get("command", "")
        if command:
            maybe_set_dirty(command)
    except Exception:
        pass  # Silent on unexpected errors


if __name__ == "__main__":
    main()
