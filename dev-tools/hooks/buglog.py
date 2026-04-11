#!/usr/bin/env python3
"""Claude Code buglog hook: pre-read bug-fix history injection and post-write recording.

Handles both PreToolUse (Bash tool) and PostToolUse (Bash tool) events in a
single script, selected by the hook_event_name field in stdin JSON.

Registration in ~/.claude/settings.json:
  "PreToolUse": [
    {"matcher": "Bash", "hooks": [{"type": "command",
        "command": "<claude-config-repo>/malte/hooks/buglog.py"}]}
  ],
  "PostToolUse": [
    {"matcher": "Bash", "hooks": [{"type": "command",
        "command": "<claude-config-repo>/malte/hooks/buglog.py"}]}
  ]

buglog.json schema: {cwd}/.claude/buglog.json
  {
    "entries": [
      {
        "id": "uuid4-string",
        "timestamp": "ISO8601",
        "error_pattern": "ImportError: cannot import name X",
        "root_cause": "circular import in module Y",
        "fix": "moved import to function scope",
        "files": ["/abs/path/to/file.py"],
        "tags": ["import", "circular"]
      }
    ]
  }

Session state: {tempdir}/claude-buglog-session-{safe_session_id}.json
  {
    "session_id": "...",
    "last_command": "pytest tests/",
    "last_stderr": "ImportError: ...",
    "had_debug_pattern": true
  }

Performance: must complete within 100ms.
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

SESSION_PREFIX = str(Path(tempfile.gettempdir()) / "claude-buglog-session-")
MAX_ENTRIES = 200

# Debug patterns: commands that indicate debugging / test running activity
DEBUG_PATTERNS = [
    r"\bpytest\b",
    r"\buv\s+run\s+pytest\b",
    r"\bruff\b",
    r"\bmypy\b",
    r"\btraceback\b",
    r"\bdebug\b",   # matches 'debug' as a whole word (not inside paths like debugger/)
    r"--tb\b",      # matches --tb= flags
    r"\bpytest\b.*\s-v\b",  # matches -v only in pytest invocations
]

# Fix commit keywords (in git commit message)
FIX_COMMIT_KEYWORDS = ["fix", "bug", "resolve", "patch", "correct"]


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def _safe_session_id(session_id: str) -> str:
    """Sanitize session_id for use in file names (whitelist: alphanumeric, _ and -)."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", session_id)


def _load_session(session_id: str) -> dict:
    """Load session state from disk, returning empty default if absent or corrupt."""
    path = Path(f"{SESSION_PREFIX}{_safe_session_id(session_id)}.json")
    if not path.exists():
        return {"session_id": session_id, "had_debug_pattern": False, "last_command": "", "last_stderr": ""}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {"session_id": session_id, "had_debug_pattern": False, "last_command": "", "last_stderr": ""}


def _save_session(session_id: str, state: dict) -> None:
    """Atomically write session state to disk via .tmp rename."""
    path = Path(f"{SESSION_PREFIX}{_safe_session_id(session_id)}.json")
    tmp_file = path.with_suffix(".tmp")
    try:
        tmp_file.write_text(json.dumps(state))
        tmp_file.replace(path)
    except OSError as e:
        tmp_file.unlink(missing_ok=True)
        print(f"buglog: session save failed: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# buglog.json path + I/O
# ---------------------------------------------------------------------------

def get_buglog_path(cwd: str) -> Path | None:
    """Return the buglog.json path for the given cwd, or None if .claude/ doesn't exist."""
    dot_claude = Path(cwd) / ".claude"
    if not dot_claude.is_dir():
        return None
    return dot_claude / "buglog.json"


def load_buglog(cwd: str) -> list[dict]:
    """Load entries from buglog.json, returning empty list on any failure."""
    path = get_buglog_path(cwd)
    if path is None or not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data.get("entries", [])
    except (json.JSONDecodeError, OSError):
        return []


def _save_buglog(path: Path, entries: list[dict]) -> None:
    """Atomically write entries to buglog.json via .tmp rename."""
    tmp_file = path.with_suffix(".tmp")
    try:
        tmp_file.write_text(json.dumps({"entries": entries}, indent=2))
        tmp_file.replace(path)
    except OSError as e:
        tmp_file.unlink(missing_ok=True)
        print(f"buglog: save failed: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Debug pattern detection
# ---------------------------------------------------------------------------

def is_debug_command(command: str) -> bool:
    """Return True if command contains any recognized debug patterns."""
    for pattern in DEBUG_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def is_fix_commit(command: str) -> bool:
    """Return True if command is a git commit with fix-related keywords in the message."""
    if not re.search(r"\bgit\s+commit\b", command):
        return False
    # Check fix keywords anywhere in the full command (handles both -m and HEREDOC-style commits)
    return any(kw in command.lower() for kw in FIX_COMMIT_KEYWORDS)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def _score_entry(entry: dict, query_keywords: set[str]) -> int:
    """Score an entry by counting matching keywords from the query.

    Matches against error_pattern and tags only (per spec), to avoid
    false positives from fix/root_cause text containing common words.
    """
    if not query_keywords:
        return 0
    target = " ".join([
        entry.get("error_pattern", ""),
        " ".join(entry.get("tags", [])),
    ]).lower()
    return sum(1 for kw in query_keywords if kw in target)


def search_buglog(entries: list[dict], query: str) -> list[dict]:
    """Search entries by keyword match against query string. Returns top 3 by score."""
    if not entries or not query.strip():
        return []
    keywords = {w.lower() for w in re.split(r"\W+", query) if len(w) > 2}
    scored = [(e, _score_entry(e, keywords)) for e in entries]
    matched = [(e, s) for e, s in scored if s > 0]
    matched.sort(key=lambda x: x[1], reverse=True)
    return [e for e, _ in matched[:3]]


def format_injection_text(matches: list[dict]) -> str:
    """Format matched entries as a numbered injection text block."""
    lines = ["Past bug fixes that may be relevant:\n"]
    for i, entry in enumerate(matches, 1):
        lines.append(f"{i}. Error: {entry.get('error_pattern', '')}")
        if entry.get("root_cause"):
            lines.append(f"   Root cause: {entry['root_cause']}")
        if entry.get("fix"):
            lines.append(f"   Fix: {entry['fix']}")
        if entry.get("files"):
            lines.append(f"   Files: {', '.join(entry['files'])}")
        lines.append("")
    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# Record fix
# ---------------------------------------------------------------------------

def record_fix(
    *,
    cwd: str,
    error_pattern: str,
    root_cause: str,
    fix: str,
    files: list[str],
    tags: list[str],
) -> None:
    """Append a new fix entry to buglog.json. Silently skips if .claude/ doesn't exist."""
    path = get_buglog_path(cwd)
    if path is None:
        return

    entries = load_buglog(cwd)

    entry: dict = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "error_pattern": error_pattern,
        "root_cause": root_cause,
        "fix": fix,
        "files": files,
        "tags": tags,
    }
    entries.append(entry)

    # AK6: enforce 200-entry FIFO cap
    entries = entries[-MAX_ENTRIES:]

    _save_buglog(path, entries)


# ---------------------------------------------------------------------------
# Backlink: write bead_id to matching buglog entries
# ---------------------------------------------------------------------------

def write_backlink(*, cwd: str, bead_id: str, error_pattern: str) -> None:
    """Write bead_id to matching buglog.json entries (substring match on error_pattern).

    Silently returns if:
    - No buglog.json exists
    - No matching entries found
    - Matching entry already has a bead_id (no overwrite)
    """
    if not error_pattern:
        return

    path = get_buglog_path(cwd)
    if path is None or not path.exists():
        return

    entries = load_buglog(cwd)
    if not entries:
        return

    modified = False
    for entry in entries:
        if "bead_id" in entry:
            continue
        stored = entry.get("error_pattern", "")
        if not stored:
            continue
        # Bidirectional substring match: caller may pass a longer or shorter string
        if error_pattern in stored or stored in error_pattern:
            entry["bead_id"] = bead_id
            modified = True

    if modified:
        _save_buglog(path, entries)


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

def handle_pre_tool_use(event: dict) -> None:
    """Handle PreToolUse Bash event — inject relevant bug history if command matches debug patterns."""
    tool_name = event.get("tool_name", "")
    if tool_name != "Bash":
        return

    tool_input = event.get("tool_input", {})
    command = tool_input.get("command", "")
    session_id = event.get("session_id", "")
    cwd = event.get("cwd", "")

    # Load session state once — reuse for both reading last_stderr and updating
    state = _load_session(session_id) if session_id else {}
    last_stderr = state.get("last_stderr", "")

    # Save current command context to session state
    is_debug = is_debug_command(command)
    if session_id:
        state["last_command"] = command
        state["had_debug_pattern"] = is_debug
        state["last_stderr"] = ""  # will be populated by PostToolUse
        _save_session(session_id, state)

    if not is_debug or not cwd:
        return

    # Build search query from current command + last session stderr
    query = f"{command} {last_stderr}"

    entries = load_buglog(cwd)
    if not entries:
        return

    matches = search_buglog(entries, query)
    if not matches:
        return

    text = format_injection_text(matches)
    print(json.dumps({"type": "text", "text": text}))


def handle_post_tool_use(event: dict) -> None:
    """Handle PostToolUse Bash event — detect fixes and record to buglog.json."""
    tool_name = event.get("tool_name", "")
    if tool_name != "Bash":
        return

    tool_input = event.get("tool_input", {})
    command = tool_input.get("command", "")
    tool_response = event.get("tool_response", {})
    stdout = tool_response.get("stdout", "")
    stderr = tool_response.get("stderr", "")
    exit_code = tool_response.get("exit_code", -1)
    session_id = event.get("session_id", "")
    cwd = event.get("cwd", "")

    if not cwd:
        return

    # Load previous session state
    session_state = _load_session(session_id) if session_id else {}
    had_debug = session_state.get("had_debug_pattern", False)
    last_stderr = session_state.get("last_stderr", "")

    fix_recorded = False

    # Case 1: Previous command was debug + this command succeeded → record fix
    if had_debug and exit_code == 0 and last_stderr.strip():
        record_fix(
            cwd=cwd,
            error_pattern=last_stderr[:200],  # truncate very long errors
            root_cause="",
            fix=f"Command succeeded: {command[:100]}",
            files=[],
            tags=_extract_tags(last_stderr),
        )
        fix_recorded = True

    # Case 2: git commit with fix keywords
    if not fix_recorded and is_fix_commit(command):
        msg_match = re.search(r"-m\s+['\"](.+?)['\"]", command, re.DOTALL)
        if msg_match:
            commit_msg = msg_match.group(1)
        else:
            # Try HEREDOC extraction: text between EOF markers
            heredoc_match = re.search(r"<<['\"]?EOF['\"]?\n(.*?)\nEOF", command, re.DOTALL)
            if heredoc_match:
                commit_msg = heredoc_match.group(1).strip()
            else:
                # Fallback: first 100 chars of command
                commit_msg = command[:100]
        record_fix(
            cwd=cwd,
            error_pattern=last_stderr[:200] if last_stderr.strip() else "unknown error",
            root_cause="",
            fix=commit_msg[:200],
            files=[],
            tags=_extract_tags(last_stderr + " " + commit_msg),
        )

    # Update session state: save current stderr for next round (reuse already-loaded session_state)
    if session_id:
        session_state["last_stderr"] = stderr
        session_state["last_command"] = command
        session_state["had_debug_pattern"] = is_debug_command(command)
        _save_session(session_id, session_state)


def _extract_tags(text: str) -> list[str]:
    """Extract simple keyword tags from error text."""
    tags = []
    tag_patterns = {
        "import": r"\bimport\b",
        "circular": r"\bcircular\b",
        "keyerror": r"\bKeyError\b",
        "typeerror": r"\bTypeError\b",
        "attributeerror": r"\bAttributeError\b",
        "valueerror": r"\bValueError\b",
        "nameerror": r"\bNameError\b",
        "syntax": r"\bSyntaxError\b",
        "assertion": r"\bAssertionError\b",
        "timeout": r"\btimeout\b",
        "connection": r"\bconnection\b",
        "permission": r"\bPermission\b",
        "filenotfound": r"\bFileNotFoundError\b",
    }
    for tag, pattern in tag_patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            tags.append(tag)
    return tags


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Main hook entry point — reads stdin JSON and dispatches to handler."""
    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError, ValueError):
        return

    event_name = event.get("hook_event_name", "")

    try:
        if event_name == "PreToolUse":
            handle_pre_tool_use(event)
        elif event_name == "PostToolUse":
            handle_post_tool_use(event)
    except Exception as e:
        # Never crash — hooks must be silent on unexpected errors
        print(f"buglog: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
