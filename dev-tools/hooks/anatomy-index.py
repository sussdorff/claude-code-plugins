#!/usr/bin/env python3
"""Claude Code anatomy-index hook: pre-read context injection and post-write index updates.

Handles both PreToolUse (Read tool) and PostToolUse (all tools) events in a
single script, selected by the hook_event_name field in stdin JSON.

Merges functionality from the former read-tracker.py hook:
- Tool-call distance tracking: counts all PostToolUse events per session
- Dedup warning with distance: "You read this file N tool calls ago and it has not changed."
- Single file I/O per PreToolUse Read event (no double-hashing)

Registration in ~/.claude/settings.json:
  "PreToolUse": [
    {"matcher": "Read", "hooks": [{"type": "command",
        "command": "<claude-config-repo>/malte/hooks/anatomy-index.py"}]}
  ],
  "PostToolUse": [
    {"matcher": "", "hooks": [{"type": "command",
        "command": "<claude-config-repo>/malte/hooks/anatomy-index.py"}]}
  ]

Anatomy index: {cwd}/.claude/anatomy.json
  {
    "/abs/path/to/file.py": {
      "line_count": 150,
      "token_estimate": 1200,
      "summary": "Brief description of file contents",
      "last_modified": "2026-04-06T10:00:00+00:00",
      "last_read": "2026-04-06T10:05:00+00:00"
    }
  }

Session state (unified): /tmp/claude-hook-session-{safe_session_id}.json
  {
    "session_id": "...",
    "tool_call_count": 42,
    "reads": {
      "/abs/path/to/file": {
        "first_tool_call": 5,
        "last_tool_call": 5,
        "content_hash": "sha256:...",
        "timestamp": "2026-04-06T..."
      }
    }
  }

Performance: must complete within 100ms.
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SESSION_PREFIX = os.environ.get("CLAUDE_HOOK_SESSION_PREFIX", "/tmp/claude-hook-session-")
SESSION_MAX_AGE_SECONDS = 86400  # 24 hours


def _safe_session_id(session_id: str) -> str:
    """Sanitize session_id for use in file names (whitelist: alphanumeric, _ and -)."""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', session_id)


def _session_path(session_id: str) -> Path:
    """Return the session state file path for the given session."""
    return Path(f"{SESSION_PREFIX}{_safe_session_id(session_id)}.json")


def _load_session(session_id: str) -> dict:
    """Load session state from disk, returning empty default if absent or corrupt."""
    path = _session_path(session_id)
    if not path.exists():
        return {"session_id": session_id, "tool_call_count": 0, "reads": {}}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {"session_id": session_id, "tool_call_count": 0, "reads": {}}


def _cleanup_old_sessions() -> None:
    """Remove hook session files older than SESSION_MAX_AGE_SECONDS from /tmp."""
    cutoff = datetime.now().timestamp() - SESSION_MAX_AGE_SECONDS
    try:
        for p in Path("/tmp").glob("claude-hook-session-*.json"):
            try:
                if p.stat().st_mtime < cutoff:
                    p.unlink(missing_ok=True)
            except OSError:
                pass
    except OSError:
        pass


def _save_session(session_id: str, state: dict) -> None:
    """Atomically write session state to disk via .tmp replace."""
    path = _session_path(session_id)
    tmp_path = path.with_suffix(".tmp")
    try:
        tmp_path.write_text(json.dumps(state))
        tmp_path.replace(path)
    except OSError as e:
        tmp_path.unlink(missing_ok=True)
        print(f"anatomy-index: session save failed: {e}", file=sys.stderr)


def _anatomy_path(cwd: str) -> Path | None:
    """Return .claude/anatomy.json path for given cwd, or None if .claude/ doesn't exist."""
    dot_claude = Path(cwd) / ".claude"
    if not dot_claude.is_dir():
        return None
    return dot_claude / "anatomy.json"


def _load_anatomy(cwd: str) -> dict:
    """Load anatomy.json for cwd, returning empty dict if absent or corrupt."""
    path = _anatomy_path(cwd)
    if path is None or not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save_anatomy(cwd: str, anatomy: dict) -> None:
    """Atomically write anatomy.json to {cwd}/.claude/anatomy.json."""
    path = _anatomy_path(cwd)
    if path is None:
        # .claude/ dir doesn't exist — silently skip
        return
    tmp_path = path.with_suffix(".tmp")
    try:
        tmp_path.write_text(json.dumps(anatomy, indent=2))
        tmp_path.replace(path)
    except OSError as e:
        tmp_path.unlink(missing_ok=True)
        print(f"anatomy-index: anatomy save failed: {e}", file=sys.stderr)


_MAX_HASH_BYTES = 10 * 1024 * 1024  # 10 MB — skip hashing larger files


def _hash_file(file_path: str) -> str | None:
    """Return sha256 hex digest of a file's bytes, or None on failure or if file > 10 MB."""
    try:
        p = Path(file_path)
        if p.stat().st_size > _MAX_HASH_BYTES:
            return None
        data = p.read_bytes()
        return "sha256:" + hashlib.sha256(data).hexdigest()
    except OSError:
        return None


def _read_file_once(file_path: str) -> tuple[str | None, str | None]:
    """Read a file in one I/O call, returning (text, sha256_hash).

    Returns (None, None) on read failure. Returns (text, None) if the file
    exceeds _MAX_HASH_BYTES to avoid blowing the 100ms hook budget on huge files.
    """
    try:
        data = Path(file_path).read_bytes()
    except OSError:
        return None, None
    text = data.decode("utf-8", errors="replace")
    if len(data) > _MAX_HASH_BYTES:
        return text, None
    return text, "sha256:" + hashlib.sha256(data).hexdigest()


def _compute_line_count(content: str) -> int:
    """Count lines in content using splitlines (handles missing trailing newlines)."""
    return len(content.splitlines())


def _compute_token_estimate(content: str) -> int:
    """Estimate token count as len(content) // 4."""
    return len(content) // 4


def _extract_summary(file_path: str, content: str) -> str:
    """Extract a brief summary from file content using heuristics by file type."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".py":
        return _summary_python(content)
    elif ext in (".sh", ".bash", ".zsh"):
        return _summary_shell(content)
    elif ext in (".md", ".markdown"):
        return _summary_markdown(content)
    elif ext == ".json":
        return _summary_json(content)
    elif ext in (".yml", ".yaml"):
        return _summary_yaml(content)
    else:
        return _summary_generic(content)


def _summary_python(content: str) -> str:
    """Extract Python module docstring or first comment block."""
    lines = content.splitlines()
    # Try to find module docstring: first triple-quoted string
    stripped = content.lstrip()
    for quote in ('"""', "'''"):
        if stripped.startswith(quote):
            end = stripped.find(quote, len(quote))
            if end != -1:
                docstring = stripped[len(quote):end].strip()
                # Take first sentence/line
                first_line = docstring.splitlines()[0].strip() if docstring else ""
                if first_line:
                    return first_line[:100]

    # Fall back to first comment block
    comments = []
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith("#") and not stripped_line.startswith("#!"):
            comments.append(stripped_line.lstrip("#").strip())
        elif comments:
            break
    if comments:
        return " ".join(comments)[:100]

    return _summary_generic(content)


def _summary_shell(content: str) -> str:
    """Extract first comment block after shebang."""
    comments = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#!"):
            continue
        if stripped.startswith("#"):
            comments.append(stripped.lstrip("#").strip())
        elif comments:
            break
    if comments:
        return " ".join(comments)[:100]
    return _summary_generic(content)


def _summary_markdown(content: str) -> str:
    """Extract first heading + first paragraph sentence."""
    parts = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if heading:
                parts.append(heading)
                continue
        if stripped and parts:
            # First non-empty line after heading
            sentence = stripped.split(". ")[0]
            parts.append(sentence[:80])
            break
    return " — ".join(parts)[:100] if parts else _summary_generic(content)


def _summary_json(content: str) -> str:
    """Describe JSON top-level structure."""
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return f"dict with {len(data)} keys"
        elif isinstance(data, list):
            return f"list of {len(data)} items"
        else:
            return f"JSON {type(data).__name__}"
    except (json.JSONDecodeError, ValueError):
        return _summary_generic(content)


def _summary_yaml(content: str) -> str:
    """Describe YAML top-level structure by counting top-level keys.

    Note: Uses line-based heuristics (non-indented lines containing a colon that
    are not comments). Limitations: misidentifies list items with colons, multi-line
    scalar values, and anchor/alias lines as top-level keys. Intended as a rough
    structural hint only — not a substitute for a proper YAML parser.
    """
    top_level_keys = 0
    for line in content.splitlines():
        if line and not line.startswith(" ") and not line.startswith("\t"):
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and ":" in stripped:
                top_level_keys += 1
    if top_level_keys > 0:
        return f"dict with {top_level_keys} keys"
    return _summary_generic(content)


def _summary_generic(content: str) -> str:
    """First non-empty, non-comment line up to 80 chars."""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("//"):
            return stripped[:80]
    return ""


def handle_pre_tool_use(event: dict) -> None:
    """Handle PreToolUse Read event — inject anatomy context and check for dedup.

    Prints file metadata from anatomy.json (line_count, token_estimate, summary,
    last_read) and warns if the same file was already read this session without
    intervening writes.
    Exits 0 in all cases (never blocks the read).
    """
    session_id = event.get("session_id", "")
    tool_input = event.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    cwd = event.get("cwd", "")

    if not file_path:
        return

    # Load anatomy.json (graceful fallback on missing/corrupt)
    anatomy = {}
    if cwd:
        anatomy = _load_anatomy(cwd)

    entry = anatomy.get(file_path)

    lines = []

    if entry:
        line_count = entry.get("line_count", "?")
        token_estimate = entry.get("token_estimate", "?")
        summary = entry.get("summary", "")
        last_read = entry.get("last_read", "")

        lines.append(
            f"[Anatomy] {Path(file_path).name}: "
            f"{line_count} lines, ~{token_estimate} tokens"
        )
        if summary:
            lines.append(f"  Summary: {summary}")
        if last_read:
            # Format: show date + time compactly
            try:
                dt = datetime.fromisoformat(last_read).astimezone(timezone.utc)
                lines.append(f"  Last read: {dt.strftime('%Y-%m-%d %H:%M UTC')}")
            except ValueError:
                lines.append(f"  Last read: {last_read}")

    # Single I/O call for both hash (dedup) and content (new anatomy entry).
    # Also enforces the size guard: files > _MAX_HASH_BYTES get no hash (treated as
    # untracked for dedup) but their text is still available for metadata.
    file_content, current_hash = _read_file_once(file_path)

    # Dedup check: has this file been read this session without changes?
    if session_id:
        session = _load_session(session_id)
        reads = session.get("reads", {})
        prev_record = reads.get(file_path)

        if prev_record is not None:
            # File was read before in this session — check if it changed
            stored_hash = prev_record.get("content_hash")
            if current_hash and current_hash == stored_hash:
                distance = session.get("tool_call_count", 0) - prev_record.get("last_tool_call", 0)
                lines.append(
                    f"[Read tracker] You read this file {distance} tool calls ago"
                    " and it has not changed."
                )
            elif current_hash and current_hash != stored_hash:
                lines.append(
                    "[Read tracker] You read this file before but it was modified"
                    " since — re-read is warranted."
                )

        # Record this read in session state (hash + tool_call_count for distance tracking).
        # Record unconditionally — even for files >10MB where _hash_file returns None
        # (we store an empty-string hash). This ensures the read-before-edit hook
        # (PreToolUse) sees the file as "read" even when hashing was skipped.
        now = datetime.now(timezone.utc).isoformat()
        current_count = session.get("tool_call_count", 0)
        existing = reads.get(file_path)
        reads[file_path] = {
            "first_tool_call": existing.get("first_tool_call", current_count) if existing else current_count,
            "last_tool_call": current_count,
            "content_hash": current_hash or "",
            "timestamp": now,
        }
        session["reads"] = reads
        _save_session(session_id, session)

        # Update last_read in anatomy.json (AK4: timestamp reflects actual reads)
        if cwd:
            existing_entry = anatomy.get(file_path)
            if existing_entry is not None:
                existing_entry["last_read"] = now
                anatomy[file_path] = existing_entry
            elif file_content is not None:
                # No existing entry — build metadata from the already-read content
                try:
                    anatomy[file_path] = {
                        "line_count": _compute_line_count(file_content),
                        "token_estimate": _compute_token_estimate(file_content),
                        "summary": _extract_summary(file_path, file_content),
                        "last_modified": datetime.fromtimestamp(
                            Path(file_path).stat().st_mtime, tz=timezone.utc
                        ).isoformat(),
                        "last_read": now,
                    }
                except OSError:
                    pass  # Skip anatomy update if stat fails
            _save_anatomy(cwd, anatomy)

    if lines:
        print("\n".join(lines))


def _update_session_counters(session_id: str, tool_name: str, tool_input: dict) -> None:
    """Increment tool_call_count and update session read/write records.

    Always increments tool_call_count for accurate distance tracking.
    For Read: records the confirmed read with hash + tool_call counts (PostToolUse
    is the definitive completion; PreToolUse may have already written a preliminary
    record — this overwrites it intentionally).
    For Write/Edit: clears the read record so the file is treated as unread next time.
    """
    if not session_id:
        return

    session = _load_session(session_id)
    session["tool_call_count"] = session.get("tool_call_count", 0) + 1
    current_count = session["tool_call_count"]
    event_file_path = tool_input.get("file_path", "")

    if tool_name == "Read" and event_file_path:
        reads = session.setdefault("reads", {})
        existing = reads.get(event_file_path)
        # Reuse PreToolUse hash if available; fall back to re-hashing if falsy (e.g. >10MB file).
        content_hash = (existing or {}).get("content_hash") or _hash_file(event_file_path) or ""
        reads[event_file_path] = {
            "first_tool_call": existing.get("first_tool_call", current_count) if existing else current_count,
            "last_tool_call": current_count,
            "content_hash": content_hash,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    elif tool_name in ("Write", "Edit", "MultiEdit") and event_file_path:
        # After editing, update the read record with the new file hash.
        # Popping it would force a re-read before every subsequent edit on the same file,
        # which is unnecessary: the edit itself means we know the current file contents.
        reads = session.setdefault("reads", {})
        existing = reads.get(event_file_path)
        new_hash = _hash_file(event_file_path) or ""
        reads[event_file_path] = {
            "first_tool_call": existing.get("first_tool_call", current_count) if existing else current_count,
            "last_tool_call": current_count,
            "content_hash": new_hash,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    _save_session(session_id, session)
    # Opportunistically clean up stale session files every 100 tool calls.
    if current_count % 100 == 0:
        _cleanup_old_sessions()


def handle_post_tool_use(event: dict) -> None:
    """Handle PostToolUse event — increment tool counter and update anatomy on writes.

    Step 1: update session counters + read/write records (all tools).
    Step 2: update anatomy.json metadata (Write/Edit only).

    Registered with empty matcher ("") to count ALL tool calls.
    """
    session_id = event.get("session_id", "")
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})
    cwd = event.get("cwd", "")

    _update_session_counters(session_id, tool_name, tool_input)

    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return

    anatomy_file_path = tool_input.get("file_path", "")

    if not anatomy_file_path or not cwd:
        return

    # Check .claude/ dir exists
    dot_claude = Path(cwd) / ".claude"
    if not dot_claude.is_dir():
        return  # silently skip

    # Read content from disk (most reliable source after write)
    try:
        content = Path(anatomy_file_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return

    line_count = _compute_line_count(content)
    token_estimate = _compute_token_estimate(content)
    summary = _extract_summary(anatomy_file_path, content)
    now = datetime.now(timezone.utc).isoformat()

    anatomy = _load_anatomy(cwd)
    existing = anatomy.get(anatomy_file_path, {})

    anatomy[anatomy_file_path] = {
        "line_count": line_count,
        "token_estimate": token_estimate,
        "summary": summary,
        "last_modified": now,
        # Preserve last_read from existing entry if present
        "last_read": existing.get("last_read", now),
    }

    _save_anatomy(cwd, anatomy)


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
        print(f"anatomy-index: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
