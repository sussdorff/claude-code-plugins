#!/usr/bin/env python3
"""Ingest Codex CLI token + cost data from @ccusage/codex into metrics.db.

@ccusage/codex (https://www.npmjs.com/package/@ccusage/codex) reads Codex JSONL
from ~/.codex and emits aggregated per-session JSON. Unlike ccusage-for-Claude,
the Codex tool does NOT expose cwd — sessions are keyed only by timestamp UUID.
Bead-id attribution therefore REQUIRES a --bead flag plus a time window. The
caller (session-close Step 16b) passes the bead's claim timestamp.

Each Codex session in the --since window is attributed to --bead. If multiple
beads ran in parallel within the same window, tokens will be over-attributed
(a known limitation — the raw data does not permit cwd-based disambiguation).

Usage:
    python3 ingest_codex.py --bead <id> [--since YYYYMMDD] [--until YYYYMMDD] [--dry-run]

--bead is REQUIRED. Without it we refuse to write (see above — no cwd means
no safe auto-attribution).

Exit code: always 0 (non-blocking for session-close). Failures print a warning.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from metrics import DB_PATH, init_db, upsert_ccusage_row  # noqa: E402


def find_codex_cli() -> list[str] | None:
    """Return the command to invoke @ccusage/codex, or None if unavailable."""
    if shutil.which("ccusage-codex"):
        return ["ccusage-codex"]
    bun_bin = Path.home() / ".bun" / "bin" / "ccusage-codex"
    if bun_bin.exists():
        return [str(bun_bin)]
    if shutil.which("bunx"):
        return ["bunx", "@ccusage/codex"]
    if shutil.which("npx"):
        return ["npx", "@ccusage/codex@latest"]
    return None


def call_codex(cmd: list[str], since: str | None, until: str | None) -> dict | None:
    """Invoke `<cmd> session --json`, return parsed JSON or None."""
    full = [*cmd, "session", "--json"]
    if since:
        full += ["--since", since]
    if until:
        full += ["--until", until]
    try:
        proc = subprocess.run(  # noqa: S603
            full,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        print(f"ingest_codex: codex CLI failed: {exc}", file=sys.stderr)
        return None

    if proc.returncode != 0:
        print(
            f"ingest_codex: codex CLI exited {proc.returncode}: "
            f"{proc.stderr.strip()[:200]}",
            file=sys.stderr,
        )
        return None

    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        print(f"ingest_codex: could not parse codex JSON: {exc}", file=sys.stderr)
        return None


def add_existing_tokens(db_path: Path, bead_id: str, date_str: str) -> tuple[int, float, int, int, int]:
    """Read the current totals for a (bead, date) row to add Codex on top of ccusage.

    Returns (total, cost, cache_read, cache_create, reasoning).
    """
    if not db_path.exists():
        return (0, 0.0, 0, 0, 0)
    conn = init_db(db_path)
    try:
        cur = conn.execute(
            """
            SELECT total_tokens, cost_usd, cache_read_tokens,
                   cache_creation_tokens, reasoning_tokens
            FROM bead_runs
            WHERE bead_id = ? AND date = ?
            ORDER BY id DESC LIMIT 1
            """,
            (bead_id, date_str),
        )
        row = cur.fetchone()
        return row if row else (0, 0.0, 0, 0, 0)
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest Codex CLI token + cost data into metrics.db."
    )
    parser.add_argument(
        "--bead",
        required=True,
        help="Bead id to attribute all Codex sessions in the window to.",
    )
    parser.add_argument("--since", help="Start date (YYYYMMDD). Default: today.")
    parser.add_argument("--until", help="End date (YYYYMMDD), inclusive.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be upserted without touching metrics.db.",
    )
    args = parser.parse_args()

    cmd = find_codex_cli()
    if cmd is None:
        print(
            "ingest_codex: ccusage-codex not found (tried PATH, ~/.bun/bin, bunx, npx) — skipping",
            file=sys.stderr,
        )
        return 0

    if not DB_PATH.exists():
        print(f"ingest_codex: metrics DB {DB_PATH} does not exist — skipping", file=sys.stderr)
        return 0

    since = args.since or date.today().strftime("%Y%m%d")
    data = call_codex(cmd, since, args.until)
    if data is None:
        return 0

    sessions = data.get("sessions", [])
    if not sessions:
        print(f"ingest_codex: no Codex sessions for {args.bead} in window", file=sys.stderr)
        return 0

    # Aggregate across sessions in the window
    total_input = 0
    total_cached_input = 0
    total_output = 0
    total_reasoning = 0
    total_tokens_sum = 0
    total_cost = 0.0
    last_activity = ""

    for s in sessions:
        total_input += int(s.get("inputTokens", 0))
        total_cached_input += int(s.get("cachedInputTokens", 0))
        total_output += int(s.get("outputTokens", 0))
        total_reasoning += int(s.get("reasoningOutputTokens", 0))
        total_tokens_sum += int(s.get("totalTokens", 0))
        total_cost += float(s.get("costUSD", 0.0))
        la = s.get("lastActivity", "")
        if la > last_activity:
            last_activity = la

    date_str = last_activity.split("T", 1)[0] if "T" in last_activity else str(date.today())

    # Codex costs/tokens are additive with Claude ccusage data for the same bead.
    # Read current row, sum, then upsert.
    prior = add_existing_tokens(DB_PATH, args.bead, date_str)
    new_total = prior[0] + total_tokens_sum
    new_cost = prior[1] + total_cost
    new_cache_read = prior[2] + total_cached_input  # Codex calls it cachedInputTokens
    new_cache_create = prior[3]  # Codex has no cache-creation distinction
    new_reasoning = prior[4] + total_reasoning

    if args.dry_run:
        print(
            f"DRY-RUN: {args.bead} date={date_str} "
            f"codex_total={total_tokens_sum} codex_cost=${total_cost:.2f} "
            f"codex_reasoning={total_reasoning} → new_row_total={new_total} new_row_cost=${new_cost:.2f}"
        )
        return 0

    try:
        result = upsert_ccusage_row(
            bead_id=args.bead,
            date_str=date_str,
            total_tokens=new_total,
            cost_usd=new_cost,
            cache_read_tokens=new_cache_read,
            cache_creation_tokens=new_cache_create,
            reasoning_tokens=new_reasoning,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"ingest_codex: upsert failed for {args.bead}: {exc}", file=sys.stderr)
        return 0

    print(
        f"ingest_codex: {result} {args.bead} date={date_str} "
        f"+codex_tokens={total_tokens_sum} +codex_cost=${total_cost:.2f} "
        f"+reasoning={total_reasoning}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
