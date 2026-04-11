#!/usr/bin/env python3
"""Read-Before-Edit PreToolUse hook.

Blocks Edit and Write tool calls on files that have not been read in the
current session. Ensures Claude always reads a file before modifying it,
preventing blind edits based on stale context.

Fail-secure: any error (JSON parse failure, missing fields, OS error) causes
exit 2 (block), not exit 0 (allow). A broken safety check should deny, not
silently pass.

Session state format (shared with anatomy-index.py):
  /tmp/claude-hook-session-{safe_session_id}.json
  {
    "session_id": "...",
    "tool_call_count": 42,
    "reads": {
      "/abs/path/to/file.py": {
        "first_tool_call": 5,
        "last_tool_call": 5,
        "content_hash": "sha256:...",
        "timestamp": "2026-04-06T..."
      }
    }
  }

Exit codes (per hook-exit-codes.md):
  0 — allow (file was read, or new file creation)
  2 — block (file not read in this session, or any error)

Registration in ~/.claude/settings.json:
  "PreToolUse": [
    {"matcher": "Edit",      "hooks": [{"type": "command", "command": "<path>/read-before-edit.py"}]},
    {"matcher": "Write",     "hooks": [{"type": "command", "command": "<path>/read-before-edit.py"}]},
    {"matcher": "MultiEdit", "hooks": [{"type": "command", "command": "<path>/read-before-edit.py"}]}
  ]

Performance: must complete within 100ms.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import NoReturn


def _file_exists(path: Path) -> bool:
    """Return True if path exists on disk, False if FileNotFoundError.

    Unlike Path.exists(), this helper propagates PermissionError and other
    OSErrors so the caller can handle them as fail-secure blocks rather than
    silently treating the file as non-existent (the Python 3.11 fail-open gap).
    """
    try:
        os.stat(path)
        return True
    except FileNotFoundError:
        return False
    # PermissionError / other OSError propagates to caller → _block

SESSION_PREFIX = os.environ.get("CLAUDE_HOOK_SESSION_PREFIX", "/tmp/claude-hook-session-")


def _safe_session_id(session_id: str) -> str:
    """Sanitize session_id for use in file names (whitelist: alphanumeric, _ and -)."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", session_id)


def _session_path(session_id: str) -> Path:
    """Return the session state file path for the given session."""
    return Path(f"{SESSION_PREFIX}{_safe_session_id(session_id)}.json")


def _load_reads(session_id: str) -> dict:
    """Load the reads dict from session state.

    Returns empty dict when the session file does not exist (no reads recorded yet).
    Raises RuntimeError with a descriptive message when the file exists but cannot be
    read or parsed — callers must treat this as a block condition (fail-secure).
    """
    path = _session_path(session_id)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        return data.get("reads", {})
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as err:
        raise RuntimeError(
            f"BLOCKED: session state unreadable at {path}: {err} — try re-reading the file."
        ) from err


def _block(message: str) -> NoReturn:
    """Print block message to stderr and exit 2."""
    print(message, file=sys.stderr)
    sys.exit(2)


def main() -> None:
    """Main hook entry point — reads stdin JSON, checks read history, allow or block."""
    # Fail-secure: any JSON parse error → block
    try:
        raw = sys.stdin.read()
        event = json.loads(raw)
    except (json.JSONDecodeError, EOFError, ValueError) as e:
        _block(f"BLOCKED: read-before-edit hook could not parse hook input: {e}")

    # Extract required fields — fail-secure on any missing field
    try:
        tool_input = event["tool_input"]
        file_path: str = tool_input["file_path"]
        session_id: str = event.get("session_id", "")
        cwd: str = event.get("cwd", "")
    except (KeyError, TypeError) as e:
        _block(
            f"BLOCKED: read-before-edit hook missing required field: {e}\n"
            "Cannot verify read history without file_path — blocking as precaution."
        )

    # AK4 exemption: new file creation — if the file doesn't exist on disk, allow
    file_path_obj = Path(file_path)

    # Resolve to absolute path if needed (using cwd).
    # Block explicitly if path is relative and cwd is empty — cannot resolve safely.
    if not file_path_obj.is_absolute() and not cwd:
        _block(
            f"BLOCKED: read-before-edit hook received relative file_path '{file_path}' "
            "with no cwd — cannot resolve safely. Blocking as precaution."
        )
    if not file_path_obj.is_absolute() and cwd:
        file_path_resolved = (Path(cwd) / file_path_obj).resolve()
    else:
        file_path_resolved = file_path_obj.resolve()

    try:
        file_exists = _file_exists(file_path_resolved)
    except OSError as e:
        _block(f"BLOCKED: read-before-edit hook OS error checking file existence for {file_path}: {e}")

    if not file_exists:
        # New file creation — exempt per AK4
        sys.exit(0)

    # Load session reads — fail-secure if session_id is missing
    if not session_id:
        _block(
            "BLOCKED: Read before Edit/Write required.\n"
            f"File not read in this session: {file_path}\n"
            "Use the Read tool to read the file first, then edit it."
        )

    try:
        reads = _load_reads(session_id)
    except RuntimeError as e:
        _block(str(e))

    # Check both raw file_path AND the resolved absolute path (AK2)
    file_was_read = file_path in reads or str(file_path_resolved) in reads

    if file_was_read:
        sys.exit(0)

    _block(
        "BLOCKED: Read before Edit/Write required.\n"
        f"File not read in this session: {file_path}\n"
        "Use the Read tool to read the file first, then edit it."
    )


if __name__ == "__main__":
    main()
