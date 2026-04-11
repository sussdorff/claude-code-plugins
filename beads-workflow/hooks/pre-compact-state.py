#!/usr/bin/env python3
"""Claude Code PreCompact hook: save in_progress bead state before compaction.

Reads stdin JSON (session_id, cwd, transcript_path), queries in_progress beads,
and writes a recovery file to ~/.claude/compaction-state/<session_id>.json.

Optionally POSTs a memory to open-brain for cross-session recovery.
Cleans up recovery files older than 48h opportunistically.

Must complete within 10s (Claude Code hook timeout).
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OPEN_BRAIN_URL = os.environ.get("OPEN_BRAIN_URL", "https://open-brain.sussdorff.org")
API_KEY = os.environ.get("OPEN_BRAIN_API_KEY")  # None if not set; POST is skipped when missing
_DEFAULT_STATE_DIR = Path.home() / ".claude" / "compaction-state"
STATE_DIR: Path = Path(os.environ.get("COMPACTION_STATE_DIR") or str(_DEFAULT_STATE_DIR))
BD_BINARY = os.environ.get("BD_BINARY", "bd")
MAX_BEADS = 10
STALE_HOURS = 48


def _get_safe_env() -> dict:
    """Return a minimal safe environment for subprocesses."""
    return {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", str(Path.home())),
        "USER": os.environ.get("USER", ""),
        "LANG": os.environ.get("LANG", "en_US.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", ""),
    }


def derive_project(cwd: str) -> str:
    """Derive project name from working directory path."""
    return Path(cwd).name if cwd else "unknown"


def get_git_branch(cwd: str) -> str:
    """Get current git branch for the given directory.

    Returns:
        Branch name, or 'unknown' if git fails.
    """
    safe_env = _get_safe_env()
    try:
        result = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            env=safe_env,
        )
        if result.returncode == 0:
            return result.stdout.strip() or "unknown"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return "unknown"


def start_bd_server() -> None:
    """Start bd dolt server (idempotent, fail-silently)."""
    safe_env = _get_safe_env()
    try:
        subprocess.run(
            [BD_BINARY, "dolt", "start"],
            capture_output=True,
            text=True,
            timeout=8,
            env=safe_env,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass


def has_beads_dir(cwd: str) -> bool:
    """Check if cwd has a .beads/ subdirectory."""
    p = Path(cwd)
    return (p / ".beads").exists()


def fetch_in_progress_beads(cwd: str) -> list[dict]:
    """Query bd for in_progress beads.

    Returns:
        List of bead dicts. Returns [] on any error.
    """
    safe_env = _get_safe_env()
    try:
        result = subprocess.run(
            [BD_BINARY, "list", "--status=in_progress", "--json"],
            capture_output=True,
            text=True,
            timeout=8,
            cwd=cwd,
            env=safe_env,
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            if isinstance(data, list):
                return data
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, json.JSONDecodeError):
        pass
    return []


def extract_last_note(notes: str | None) -> str:
    """Extract the last non-empty paragraph or line from notes text.

    Tries double-newline paragraph splitting first; if the result is a multi-line
    block, falls through to single-line splitting to return only the final line.
    """
    if not notes:
        return ""
    # Try paragraph split first (double newlines)
    paragraphs = [p.strip() for p in notes.split("\n\n") if p.strip()]
    if len(paragraphs) > 1:
        # Multiple paragraphs — return last paragraph's last line
        last_para = paragraphs[-1]
        lines = [line.strip() for line in last_para.splitlines() if line.strip()]
        return lines[-1] if lines else last_para
    # Fall back to single-line splitting (handles single-newline separated content)
    lines = [line.strip() for line in notes.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def select_top_beads(beads: list[dict], max_count: int = MAX_BEADS) -> list[dict]:
    """Sort beads by priority (ascending) and return top max_count.

    Args:
        beads: List of bead dicts with 'priority' field.
        max_count: Maximum number of beads to return.

    Returns:
        Top beads sorted by priority.
    """
    sorted_beads = sorted(beads, key=lambda b: b.get("priority", 999))
    return sorted_beads[:max_count]


def build_recovery_record(
    session_id: str,
    cwd: str,
    beads: list[dict],
) -> dict:
    """Build the recovery file payload.

    Args:
        session_id: Claude Code session ID.
        cwd: Working directory at compaction time.
        beads: List of in_progress beads (already truncated).

    Returns:
        Recovery dict matching the recovery file schema.
    """
    branch = get_git_branch(cwd)
    in_progress = [
        {
            "id": b.get("id", ""),
            "title": b.get("title", ""),
            "last_note": extract_last_note(b.get("notes")),
        }
        for b in beads
    ]
    return {
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": derive_project(cwd),
        "branch": branch,
        "in_progress_beads": in_progress,
    }


def write_recovery_file(session_id: str, record: dict) -> None:
    """Write recovery record to the state directory.

    Args:
        session_id: Used as filename (<session_id>.json).
        record: Recovery data dict.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    outfile = STATE_DIR / f"{session_id}.json"
    outfile.write_text(json.dumps(record, indent=2))


def post_to_open_brain(session_id: str, project: str, record: dict) -> None:
    """POST a memory to open-brain (fail-silently, timeout=5s).

    Skipped entirely if OPEN_BRAIN_API_KEY env var is not set.

    Args:
        session_id: Session identifier for tagging.
        project: Project name for the memory.
        record: Recovery record to serialise as memory text.
    """
    if not API_KEY:
        return  # Skip if API key not configured

    bead_lines = "\n".join(
        f"- [{b['id']}] {b['title']}: {b['last_note']}"
        for b in record["in_progress_beads"]
    )
    text = f"Pre-compaction state snapshot for session {session_id}.\n\nProject: {project}\nBranch: {record.get('branch', 'unknown')}\n\nIn-progress beads:\n{bead_lines or '(none)'}"

    payload = json.dumps({
        "title": f"Compaction state: {project} ({session_id[:8]})",
        "text": text,
        "type": "session_summary",
        "project": project,
        "session_ref": session_id,
        "metadata": {
            "tags": ["compaction", f"session:{session_id}", f"project:{project}"],
        },
    }).encode()

    req = urllib.request.Request(
        f"{OPEN_BRAIN_URL}/api/memories",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=5):
            pass
    except Exception:
        # Non-blocking: recovery file already written, open-brain is optional
        pass


def cleanup_stale_files(max_age_hours: int = STALE_HOURS) -> None:
    """Remove recovery files older than max_age_hours (opportunistic)."""
    if not STATE_DIR.is_dir():
        return
    cutoff = time.time() - max_age_hours * 3600
    for entry in STATE_DIR.iterdir():
        try:
            if entry.is_file() and entry.suffix == ".json" and entry.stat().st_mtime < cutoff:
                entry.unlink()
        except OSError:
            pass


def main() -> None:
    """Main hook entry point — reads stdin and writes recovery state."""
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    session_id = hook_input.get("session_id", "")
    cwd = hook_input.get("cwd", "") or os.getcwd()

    # Start bd server (idempotent — safe to call even if running)
    start_bd_server()

    # Collect in_progress beads only if .beads/ exists in cwd
    beads: list[dict] = []
    if has_beads_dir(cwd):
        raw_beads = fetch_in_progress_beads(cwd)
        beads = select_top_beads(raw_beads)

    # Build and write recovery record
    record = build_recovery_record(session_id, cwd, beads)
    write_recovery_file(session_id, record)

    # Optional: POST to open-brain (fail-silently)
    project = derive_project(cwd)
    post_to_open_brain(session_id, project, record)

    # Cleanup old recovery files
    cleanup_stale_files()


if __name__ == "__main__":
    main()
