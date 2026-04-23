#!/usr/bin/env python3
"""
wave-status.py — Single-call monitoring for all beads in a wave.

Usage: wave-status.py <wave-config.json>

Input: JSON file with wave configuration:
  {
    "dispatch_time": "2026-03-30T14:00:00",
    "beads": [
      {"id": "mira-0al", "surface": "surface:3"},
      {"id": "mira-doq", "surface": "surface:5"}
    ]
  }

Output: JSON status report to stdout.

Reads all surfaces in parallel using threading.Thread.
"""

import json
import re
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

from wave_helpers import (
    _DEAD_SURFACE_RE,
    _bd_status,
    _read_surface,
    _surface_is_idle,
)


# ---------------------------------------------------------------------------
# Per-bead status check
# ---------------------------------------------------------------------------


def _check_bead(bead_id: str, surface: str, result_holder: list) -> None:
    """Check one bead's surface and bd status. Thread-safe via result_holder."""
    screen = _read_surface(surface, lines=60, scrollback=True)

    status = "unknown"
    detail = ""

    # Dead surface check
    if _DEAD_SURFACE_RE.search(screen):
        status = "dead"
        detail = "Surface terminated (pane closed)"
        screen = ""

    if status == "unknown":
        if "BLOCKED: Missing Scenario" in screen:
            status = "blocked"
            detail = "Missing scenario section"
        elif re.search(r"error|panic|fatal|traceback|ENOENT|ECONNREFUSED", screen, re.IGNORECASE):
            # Check last 5 lines for real errors
            last_lines = "\n".join(screen.splitlines()[-5:])
            if re.search(r"error|panic|fatal|traceback", last_lines, re.IGNORECASE):
                status = "failed"
                m = re.search(r"(error|panic|fatal|traceback)[^\n]*", last_lines, re.IGNORECASE)
                detail = m.group(0)[:120] if m else ""

    # Override with more specific patterns (order matters — later wins)
    if "Handoff to Session Close" in screen:
        status = "session_close"
        detail = "Implementation done, session close running"
    if re.search(r"review-agent|Review iteration|Codex review", screen):
        status = "in_review"
        m = re.search(r"iteration [0-9]+/[0-9]+", screen)
        detail = f"Review active ({m.group(0)})" if m else "Review active"
    if "session-close" in screen:
        status = "session_close"
        detail = "Session close in progress"
    if re.search(r"PIPELINE FAILED|pipeline.*failed|CI pipeline.*fail", screen, re.IGNORECASE):
        status = "pipeline_failed"
        m = re.search(r"(PIPELINE FAILED|pipeline.*failed|CI pipeline.*fail)[^\n]*", screen, re.IGNORECASE)
        detail = m.group(0)[:120] if m else ""

    if status == "unknown":
        if re.search(r"pytest|jest|vitest|bun test|Running tests|PASS|FAIL", screen):
            status = "in_progress"
            detail = "Running tests"
        elif re.search(r"Edit|Write|Bash|Read|Grep", screen):
            status = "in_progress"
            detail = "Active editing"

    # Idle check
    last_5 = "\n".join(screen.splitlines()[-5:]) if screen else ""
    if _surface_is_idle(last_5):
        status = "done"
        detail = "Shell idle, no active session"

    # Collect follow-ups
    follow_ups = re.findall(r"Created issue: ([a-zA-Z0-9_-]+)", screen)

    # BD status (authoritative for done)
    bd_st = _bd_status(bead_id)
    if bd_st == "closed":
        status = "done"
        detail = "Bead closed in database"

    result_holder.append({
        "id": bead_id,
        "surface": surface,
        "status": status,
        "detail": detail,
        "bd_status": bd_st,
        "follow_up_beads": list(set(follow_ups)),
    })


# ---------------------------------------------------------------------------
# Elapsed minutes
# ---------------------------------------------------------------------------


def _elapsed_minutes(dispatch_time: str) -> int:
    """Compute elapsed minutes from dispatch_time ISO string. Returns -1 on error."""
    try:
        # Parse ISO-8601 without timezone (UTC assumed)
        dt = datetime.strptime(dispatch_time.rstrip("Z"), "%Y-%m-%dT%H:%M:%S")
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        delta = now - dt
        return int(delta.total_seconds() / 60)
    except Exception:
        return -1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: wave-status.py <wave-config.json>", file=sys.stderr)
        return 1

    config_path = Path(sys.argv[1])
    if not config_path.is_file():
        print(f"Error: config file not found: {config_path}", file=sys.stderr)
        return 1

    try:
        config = json.loads(config_path.read_text())
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in config: {e}", file=sys.stderr)
        return 1

    dispatch_time = config.get("dispatch_time", "")
    elapsed_min = _elapsed_minutes(dispatch_time) if dispatch_time else -1

    beads = config.get("beads", [])

    # Read all surfaces in parallel
    threads: list[threading.Thread] = []
    results: list[list] = [[] for _ in beads]

    for i, bead in enumerate(beads):
        bead_id = bead.get("id", "")
        surface = bead.get("surface", "")
        t = threading.Thread(
            target=_check_bead,
            args=(bead_id, surface, results[i]),
            daemon=True,
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=60)

    bead_results = []
    all_done = True
    follow_up_beads_all: set[str] = set()

    for res_list in results:
        if res_list:
            bead_result = res_list[0]
            bead_results.append(bead_result)
            if bead_result["status"] != "done":
                all_done = False
            if bead_result["status"] == "pipeline_failed":
                all_done = False
            follow_up_beads_all.update(bead_result.get("follow_up_beads", []))

    output = {
        "elapsed_minutes": elapsed_min,
        "beads": bead_results,
        "all_done": all_done,
        "follow_up_beads": sorted(follow_up_beads_all),
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
