#!/usr/bin/env python3
"""Unified session context collector for Claude Code SessionStart hook.

Usage:
    python scripts/session-context.py [--cwd <path>]

Reads stdin (SessionStart hook JSON payload) and outputs a single JSON blob
to stdout with sections: git, beads, dolt, last_session.
Each section fails independently with {"status": "error", "message": "..."}.
"""

import argparse
import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path

_DEFAULT_STATE_DIR = Path.home() / ".claude" / "compaction-state"


def _run(cmd: list[str], cwd: str | None = None, timeout: int = 5) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr).

    Args:
        cmd: Command as a list of strings.
        cwd: Working directory.
        timeout: Timeout in seconds.

    Returns:
        Tuple of returncode, stdout (stripped), stderr (stripped).
    """
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            encoding="utf-8",
            errors="replace",
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except FileNotFoundError:
        return -1, "", f"command not found: {cmd[0]}"
    except Exception as e:
        return -1, "", str(e)


def collect_git(cwd: str) -> dict:
    """Collect git context for the given directory.

    Args:
        cwd: Working directory of the git repo.

    Returns:
        Dict with branch, ahead, behind, uncommitted, uncommitted_count.
    """
    try:
        rc, _, _ = _run(["git", "rev-parse", "--is-inside-work-tree"], cwd=cwd)
        if rc != 0:
            return {"status": "not_a_git_repo"}

        result: dict = {}

        # Branch
        rc, out, _ = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)
        result["branch"] = out if rc == 0 else "unknown"

        # Ahead/behind upstream
        rc, out, _ = _run(["git", "rev-list", "--left-right", "--count", "@{u}...HEAD"], cwd=cwd)
        if rc == 0 and "\t" in out:
            parts = out.split("\t")
            result["behind"] = int(parts[0])
            result["ahead"] = int(parts[1])
        else:
            result["ahead"] = None
            result["behind"] = None

        # Uncommitted changes
        rc, out, _ = _run(["git", "status", "--porcelain", "-u"], cwd=cwd)
        if rc == 0:
            files = [line[3:] for line in out.splitlines() if len(line) > 3]
            result["uncommitted"] = files
            result["uncommitted_count"] = len(files)
        else:
            result["uncommitted"] = []
            result["uncommitted_count"] = 0

        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


def collect_beads(cwd: str) -> dict:
    """Collect beads information from the working directory.

    Args:
        cwd: Working directory with optional .beads/ directory.

    Returns:
        Dict with open, in_progress, items.
    """
    try:
        beads_dir = Path(cwd) / ".beads"
        if not beads_dir.exists():
            return {"open": 0, "in_progress": 0, "items": []}

        items: list[dict] = []
        counts: dict[str, int] = {"open": 0, "in_progress": 0}

        for status in ("open", "in_progress"):
            rc, out, _ = _run(["bd", "list", "--status", status, "--flat"], cwd=cwd, timeout=10)
            if rc != 0:
                continue
            for line in out.splitlines():
                line = line.strip()
                if not line or line.startswith("-") or line.startswith("Total:") or line.startswith("Status:"):
                    continue
                parsed = _parse_bd_line(line)
                if parsed:
                    items.append(parsed)
                    counts[status] = counts[status] + 1

        return {
            "open": counts["open"],
            "in_progress": counts["in_progress"],
            "items": items,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _parse_bd_line(line: str) -> dict | None:
    """Parse a `bd list --flat` output line into a dict.

    Format: ○ ID [● P2] [type] - Title

    Args:
        line: Output line from `bd list --flat`.

    Returns:
        Dict with id, title, status, priority or None if no match.
    """
    m = re.match(
        r"^[○◐●✓❄]\s+"  # status icon
        r"(\S+)\s+"  # ID
        r"\[([●○◐✓❄])\s+"  # priority icon
        r"(P\d)\]\s+"  # priority
        r"(?:\[[^\]]+\]\s+)*"  # optional type/label tags
        r"-\s+"  # dash separator
        r"(.+)$",  # title
        line,
    )
    if not m:
        return None

    status_map = {
        "○": "open",
        "◐": "in_progress",
        "●": "blocked",
        "✓": "closed",
        "❄": "deferred",
    }
    status_icon = line[0]

    return {
        "id": m.group(1),
        "priority": m.group(3),
        "title": m.group(4).strip(),
        "status": status_map.get(status_icon, "unknown"),
    }


def collect_dolt(cwd: str) -> dict:
    """Check Dolt connectivity for the given directory.

    Args:
        cwd: Working directory with optional .beads/ directory.

    Returns:
        Dict with has_beads and status (ok | unreachable | no_port_info | not_configured | error).
    """
    try:
        metadata_path = Path(cwd) / ".beads" / "metadata.json"
        if not metadata_path.exists():
            return {"has_beads": False, "status": "not_configured"}

        with open(metadata_path, encoding="utf-8") as f:
            meta = json.load(f)

        result: dict = {"has_beads": True}

        # Determine port: check dolt-server.port file first, then metadata
        port: int | None = None
        host = "localhost"

        port_file = Path(cwd) / ".beads" / "dolt-server.port"
        if port_file.exists():
            try:
                port = int(port_file.read_text().strip())
            except ValueError:
                pass

        if "dolt-server" in meta and isinstance(meta["dolt-server"], dict):
            srv = meta["dolt-server"]
            host = srv.get("host", host)
            if port is None:
                port = srv.get("port")

        if port is None:
            result["status"] = "no_port_info"
            return result

        result["port"] = port
        result["server"] = host

        # Connectivity check
        try:
            s = socket.create_connection((host, port), timeout=2)
            s.close()
            result["status"] = "ok"
        except (TimeoutError, ConnectionRefusedError, OSError):
            result["status"] = "unreachable"

        return result
    except Exception as e:
        return {"has_beads": False, "status": "error", "message": str(e)}


def collect_last_session(state_dir: Path | None = None) -> dict:
    """Read the most recent compaction recovery state.

    Args:
        state_dir: Directory containing .json recovery files (default: ~/.claude/compaction-state/).

    Returns:
        Dict with date (ISO timestamp), summary or {"status": "no_sessions"}.
    """
    try:
        if state_dir is None:
            state_dir = _DEFAULT_STATE_DIR

        if not state_dir.is_dir():
            return {"status": "no_sessions"}

        candidates: list[tuple[float, Path]] = []
        for entry in state_dir.iterdir():
            if entry.is_file() and entry.suffix == ".json":
                try:
                    mtime = entry.stat().st_mtime
                    candidates.append((mtime, entry))
                except OSError:
                    continue

        if not candidates:
            return {"status": "no_sessions"}

        candidates.sort(key=lambda t: t[0], reverse=True)
        _, newest_path = candidates[0]

        try:
            data = json.loads(newest_path.read_text())
        except (json.JSONDecodeError, OSError):
            return {"status": "no_sessions"}

        date = data.get("timestamp", "")
        beads: list[dict] = data.get("in_progress_beads", [])

        if beads:
            ids = [b.get("id", "?") for b in beads]
            summary = f"{len(beads)} beads in progress: [{', '.join(ids)}]"
        else:
            summary = "No in-progress beads"

        return {"date": date, "summary": summary}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main() -> None:
    """Entry point — reads stdin, collects context, outputs JSON."""
    # Drain stdin (SessionStart hook protocol)
    try:
        _ = sys.stdin.read()
    except (OSError, EOFError):
        pass

    parser = argparse.ArgumentParser(description="Collect session context")
    parser.add_argument("--cwd", default=os.getcwd(), help="Working directory (default: cwd)")
    args = parser.parse_args()

    cwd = str(Path(args.cwd).resolve())

    # Compaction state dir can be overridden via env for tests
    state_dir_env = os.environ.get("COMPACTION_STATE_DIR")
    state_dir: Path | None = Path(state_dir_env) if state_dir_env else None

    context = {
        "git": collect_git(cwd),
        "beads": collect_beads(cwd),
        "dolt": collect_dolt(cwd),
        "last_session": collect_last_session(state_dir),
    }

    json.dump(context, sys.stdout, indent=2, ensure_ascii=False)
    print()  # trailing newline


if __name__ == "__main__":
    main()
