#!/usr/bin/env python3
"""
wave-lock.py — Single-instance guard for the wave orchestrator.

Usage:
  wave-lock.py acquire <lockfile> <wave_id> <surface>
      Fail-fast: exits 1 immediately if another live orchestrator holds the lock.
      If lock exists but holder PID is dead → warn, auto-clear, acquire.
      Exits 0 on success.

  wave-lock.py release <lockfile>
      Remove the lock. Called on clean orchestrator exit.
      Exits 0. Safe to call even if lockfile is absent.

  wave-lock.py status <lockfile>
      Print lock state JSON to stdout.
      Exits 0 regardless of lock state.

Lockfile format:
  {
    "holder": {
      "wave_id": "...",
      "surface": "...",
      "pid": 123,
      "acquired_at": "ISO-8601"
    }
  }

Error message on collision:
  Wave orchestrator already running (wave_id: ..., surface: ...).
  Do NOT start another — use beads-workflow:wave-monitor to watch progress.
"""

import fcntl
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _pid_alive(pid: int) -> bool:
    """Return True if process is alive (os.kill with signal 0)."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _read_lock(lockfile: str) -> dict:
    """Read the lockfile and return its JSON contents, or {"holder": null}."""
    path = Path(lockfile)
    if not path.exists():
        return {"holder": None}
    try:
        data = json.loads(path.read_text())
        # Normalize: ensure "holder" key exists
        if "holder" not in data:
            return {"holder": None}
        return data
    except (json.JSONDecodeError, OSError):
        return {"holder": None}


def _write_lock_atomic(lockfile: str, data: dict) -> None:
    """Write lock data atomically using a temp file + os.replace()."""
    path = Path(lockfile)
    tmp_path = path.parent / f".{path.name}.tmp.{os.getpid()}"
    tmp_path.write_text(json.dumps(data, indent=2) + "\n")
    os.replace(str(tmp_path), lockfile)


def cmd_status(lockfile: str) -> dict:
    """Print lock state JSON to stdout and return the parsed dict."""
    data = _read_lock(lockfile)
    print(json.dumps(data, indent=2))
    return data


def cmd_acquire(lockfile: str, wave_id: str, surface: str) -> int:
    """
    Acquire the lock.
    Returns 0 on success, 1 on collision (live holder).
    """
    my_pid = os.getpid()
    lock_data = _read_lock(lockfile)
    holder = lock_data.get("holder")

    # Case 1: No holder → acquire immediately
    if holder is None:
        new_lock = {
            "holder": {
                "wave_id": wave_id,
                "surface": surface,
                "pid": my_pid,
                "acquired_at": _now_iso(),
            }
        }
        _write_lock_atomic(lockfile, new_lock)
        print(
            f"==> [wave-lock] acquired (wave_id={wave_id} surface={surface} pid={my_pid})",
            file=sys.stderr,
        )
        return 0

    # Case 2: Lock exists — inspect holder
    holder_pid = holder.get("pid", 0)
    holder_wave = holder.get("wave_id", "unknown")
    holder_surface = holder.get("surface", "unknown")

    if isinstance(holder_pid, int) and holder_pid > 0 and _pid_alive(holder_pid):
        # Live holder → fail-fast
        print("", file=sys.stderr)
        print(
            f"ERROR: Wave orchestrator already running (wave_id: {holder_wave}, surface: {holder_surface}).",
            file=sys.stderr,
        )
        print(
            "Do NOT start another — use beads-workflow:wave-monitor to watch progress.",
            file=sys.stderr,
        )
        print("", file=sys.stderr)
        return 1

    # Case 3: Holder PID is dead → warn, auto-clear, acquire
    acquired_at = holder.get("acquired_at", "unknown")
    print(
        f"==> [wave-lock] WARNING: found dead holder (wave_id={holder_wave} pid={holder_pid} acquired_at={acquired_at})",
        file=sys.stderr,
    )
    print("==> [wave-lock] auto-clearing stale lock and acquiring", file=sys.stderr)

    new_lock = {
        "holder": {
            "wave_id": wave_id,
            "surface": surface,
            "pid": my_pid,
            "acquired_at": _now_iso(),
        }
    }
    _write_lock_atomic(lockfile, new_lock)
    print(
        f"==> [wave-lock] acquired after stale-clear (wave_id={wave_id} surface={surface} pid={my_pid})",
        file=sys.stderr,
    )
    return 0


def cmd_release(lockfile: str) -> int:
    """
    Release the lock.
    Returns 0 (safe to call even if lockfile is absent).
    """
    path = Path(lockfile)
    if not path.exists():
        print(
            f"==> [wave-lock] release: lockfile not found ({lockfile}) — already released or never acquired",
            file=sys.stderr,
        )
        return 0

    _write_lock_atomic(lockfile, {"holder": None})
    print("==> [wave-lock] lock released", file=sys.stderr)
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(
            "Usage: wave-lock.py <acquire|release|status> <lockfile> [<wave_id> <surface>]",
            file=sys.stderr,
        )
        return 1

    subcommand = args[0]
    rest = args[1:]

    if subcommand == "acquire":
        if len(rest) < 3:
            print(
                "Usage: wave-lock.py acquire <lockfile> <wave_id> <surface>",
                file=sys.stderr,
            )
            return 1
        return cmd_acquire(rest[0], rest[1], rest[2])

    elif subcommand == "release":
        if len(rest) < 1:
            print("Usage: wave-lock.py release <lockfile>", file=sys.stderr)
            return 1
        return cmd_release(rest[0])

    elif subcommand == "status":
        if len(rest) < 1:
            print("Usage: wave-lock.py status <lockfile>", file=sys.stderr)
            return 1
        cmd_status(rest[0])
        return 0

    else:
        print(
            "Usage: wave-lock.py <acquire|release|status> <lockfile> [<wave_id> <surface>]",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
