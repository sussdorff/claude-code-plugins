#!/usr/bin/env python3
"""turn-log-upload.py - Upload worktree turn log to open-brain.

Reads .worktree-turns.jsonl, parses each line as JSON, posts the batch to the
open-brain worktree-session-summary endpoint, and deletes the file on success.

Env vars (all required except OPEN_BRAIN_API_KEY):
  TURN_LOG          - absolute path to the .worktree-turns.jsonl file
  WORKTREE_REL      - worktree path relative to main repo
  BEAD_ID_FROM_PATH - bead id extracted from worktree dirname (may be empty)
  PROJECT_NAME      - repo name
  OPEN_BRAIN_URL    - base URL (default: https://open-brain.sussdorff.org)
  OPEN_BRAIN_API_KEY - API key (optional)

Output (stdout, single KV line):
  TURN_LOG_STATUS=empty_deleted
  TURN_LOG_STATUS=uploaded_deleted
  TURN_LOG_STATUS=error_kept parse_error=line_N:<msg>
  TURN_LOG_STATUS=error_kept status=<http_code>
  TURN_LOG_STATUS=error_kept exc=<exception>

Exit codes:
  0 - success (uploaded or empty+deleted); caller continues normally
  1 - error; file is preserved for the next session-close. Caller records
      the warning but MUST NOT abort session-close.
"""

import json
import os
import sys
import urllib.request
from pathlib import Path


def main() -> int:
    turn_log_env = os.environ.get("TURN_LOG", "")
    if not turn_log_env:
        print("TURN_LOG_STATUS=error_kept exc=missing_TURN_LOG_env")
        return 1

    turn_log = Path(turn_log_env)
    if not turn_log.exists():
        # Caller should have gated this — treat as non-error skip
        print("TURN_LOG_STATUS=empty_deleted")
        return 0

    lines = [l.strip() for l in turn_log.read_text().splitlines() if l.strip()]
    if not lines:
        turn_log.unlink()
        print("TURN_LOG_STATUS=empty_deleted")
        return 0

    # Fail-closed on malformed input — keep the file intact so a human can inspect.
    turns = []
    for i, line in enumerate(lines, 1):
        try:
            turns.append(json.loads(line))
        except json.JSONDecodeError as exc:
            print(f"TURN_LOG_STATUS=error_kept parse_error=line_{i}:{exc}")
            return 1

    worktree = os.environ.get("WORKTREE_REL", "")
    bead_id = os.environ.get("BEAD_ID_FROM_PATH", "")
    project = os.environ.get("PROJECT_NAME", "unknown")
    base_url = os.environ.get("OPEN_BRAIN_URL", "https://open-brain.sussdorff.org").rstrip("/")
    api_key = os.environ.get("OPEN_BRAIN_API_KEY", "")

    payload = json.dumps({
        "worktree": worktree,
        "bead_id": bead_id,
        "project": project,
        "turns": turns,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/api/worktree-session-summary",
        data=payload,
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)  # noqa: S310 (trusted URL)
        if resp.status == 202:
            turn_log.unlink()
            print("TURN_LOG_STATUS=uploaded_deleted")
            return 0
        print(f"TURN_LOG_STATUS=error_kept status={resp.status}")
        return 1
    except Exception as exc:  # noqa: BLE001 (non-blocking — any failure keeps file)
        print(f"TURN_LOG_STATUS=error_kept exc={exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
