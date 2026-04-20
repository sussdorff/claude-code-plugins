#!/usr/bin/env python3
"""Ingest Claude Code token + cost data from ccusage into metrics.db.

ccusage (https://www.npmjs.com/package/ccusage) reads Claude Code JSONL from
~/.claude/projects/*/*.jsonl and emits aggregated per-session JSON. We filter
sessions whose sessionId encodes a bead worktree path and UPSERT per-bead rows.

Bead-id attribution: Claude Code creates a project dir for every cwd. A bead
worktree like
    /Users/malte/code/claude-code-plugins/.claude/worktrees/bead-CCP-5ze
appears in ccusage as a sessionId
    -Users-malte-code-claude-code-plugins--claude-worktrees-bead-CCP-5ze
(slashes replaced by dashes). The regex `worktrees-bead-(?P<b>.+)$` extracts
the bead id.

Usage:
    python3 ingest_ccusage.py [--since YYYYMMDD] [--bead <id>] [--backfill] [--dry-run]

Defaults: --since=7 days ago. --backfill ignores --since. --bead filters to
a single bead id.

Exit code: always 0 (non-blocking for session-close). Failures print a warning.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Find metrics.py next to this file — works in both dev and installed layouts.
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from metrics import DB_PATH, upsert_ccusage_row  # noqa: E402

BEAD_RE = re.compile(r"worktrees-bead-(?P<b>.+)$")


def find_ccusage() -> list[str] | None:
    """Return the command to invoke ccusage, or None if unavailable."""
    if shutil.which("ccusage"):
        return ["ccusage"]
    bun_bin = Path.home() / ".bun" / "bin" / "ccusage"
    if bun_bin.exists():
        return [str(bun_bin)]
    if shutil.which("bunx"):
        return ["bunx", "ccusage"]
    if shutil.which("npx"):
        return ["npx", "ccusage@latest"]
    return None


def call_ccusage(cmd: list[str], since: str | None) -> dict | None:
    """Invoke `<cmd> session --json [--since <date>]`, return parsed JSON or None."""
    full = [*cmd, "session", "--json"]
    if since:
        full += ["--since", since]
    try:
        proc = subprocess.run(  # noqa: S603 (trusted cmd)
            full,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        print(f"ingest_ccusage: ccusage failed: {exc}", file=sys.stderr)
        return None

    if proc.returncode != 0:
        print(
            f"ingest_ccusage: ccusage exited {proc.returncode}: "
            f"{proc.stderr.strip()[:200]}",
            file=sys.stderr,
        )
        return None

    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        print(f"ingest_ccusage: could not parse ccusage JSON: {exc}", file=sys.stderr)
        return None


def extract_bead_id(session_id: str) -> str | None:
    """Extract bead id from a ccusage sessionId. None if not a bead worktree."""
    m = BEAD_RE.search(session_id)
    return m.group("b") if m else None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest Claude Code token + cost data from ccusage into metrics.db."
    )
    parser.add_argument("--since", help="Start date (YYYYMMDD). Default: 7 days ago.")
    parser.add_argument(
        "--bead", help="Restrict upsert to a single bead id (any matches are still logged)."
    )
    parser.add_argument(
        "--backfill",
        action="store_true",
        help="Ingest ALL ccusage sessions (ignores --since). Idempotent via UPSERT.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be upserted without touching metrics.db.",
    )
    args = parser.parse_args()

    cmd = find_ccusage()
    if cmd is None:
        print(
            "ingest_ccusage: ccusage not found (tried PATH, ~/.bun/bin/ccusage, bunx, npx) — skipping",
            file=sys.stderr,
        )
        return 0

    if args.backfill:
        since = None
    elif args.since:
        since = args.since
    else:
        since = (date.today() - timedelta(days=7)).strftime("%Y%m%d")

    if not DB_PATH.exists():
        print(f"ingest_ccusage: metrics DB {DB_PATH} does not exist — skipping", file=sys.stderr)
        return 0

    data = call_ccusage(cmd, since)
    if data is None:
        return 0

    sessions = data.get("sessions", [])
    if not sessions:
        print("ingest_ccusage: no sessions in window", file=sys.stderr)
        return 0

    updated = 0
    inserted = 0
    skipped_non_bead = 0
    skipped_bead_filter = 0

    for s in sessions:
        session_id = s.get("sessionId", "")
        bead_id = extract_bead_id(session_id)
        if not bead_id:
            skipped_non_bead += 1
            continue
        if args.bead and bead_id != args.bead:
            skipped_bead_filter += 1
            continue

        # Normalize date: ccusage gives 'lastActivity' like '2026-04-20'
        date_str = s.get("lastActivity") or str(date.today())
        # If it looks like full ISO, take the date portion
        if "T" in date_str:
            date_str = date_str.split("T", 1)[0]

        total = int(s.get("totalTokens", 0))
        cost = float(s.get("totalCost", 0.0))
        cache_read = int(s.get("cacheReadTokens", 0))
        cache_create = int(s.get("cacheCreationTokens", 0))

        if args.dry_run:
            print(
                f"DRY-RUN: {bead_id} date={date_str} total={total} "
                f"cost=${cost:.2f} cache_read={cache_read}"
            )
            continue

        try:
            result = upsert_ccusage_row(
                bead_id=bead_id,
                date_str=date_str,
                total_tokens=total,
                cost_usd=cost,
                cache_read_tokens=cache_read,
                cache_creation_tokens=cache_create,
                reasoning_tokens=0,  # Claude Code has no reasoning tokens
            )
        except Exception as exc:  # noqa: BLE001
            print(f"ingest_ccusage: upsert failed for {bead_id}: {exc}", file=sys.stderr)
            continue

        if result == "updated":
            updated += 1
        else:
            inserted += 1

    print(
        f"ingest_ccusage: {updated} updated, {inserted} inserted, "
        f"{skipped_non_bead} non-bead sessions, "
        f"{skipped_bead_filter} filtered out by --bead"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
