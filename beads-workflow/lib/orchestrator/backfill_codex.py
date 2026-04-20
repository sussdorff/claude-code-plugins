#!/usr/bin/env python3
"""Retroactive backfill of Codex token + cost data into metrics.db.

Codex JSONL has no cwd field, so per-session cwd-based attribution is
impossible (see ingest_codex.py for the live flow). This script performs
a retroactive, best-effort attribution by matching each Codex session's
`lastActivity` timestamp against bead windows [started_at, closed_at]
from one or more beads projects.

Attribution strategy: NARROWEST matching window wins. If a session's
timestamp falls inside multiple bead windows across projects (parallel
work), the bead with the smallest window duration is chosen. This
approximates "the bead you were focused on" better than over-counting.

Workflow contract: this script ADDS Codex tokens/cost on top of the
current row (which is assumed to be the ccusage baseline). For
deterministic re-runs, ALWAYS run `ingest_ccusage.py --backfill` FIRST
— that resets cost_usd / total_tokens / cache_* to ccusage-only values,
and zeros reasoning_tokens. Then this backfill reads that baseline and
adds Codex on top. Running ccusage-backfill+codex-backfill as a pair is
idempotent. Running this script alone twice double-counts.

Usage:
    python3 backfill_codex.py [--projects PATH ...] [--dry-run] [--since YYYYMMDD]

Defaults: --projects=cwd. No --since (all Codex sessions).

Exit code: 0 on success, 1 on fatal errors (CLI missing, JSON parse fail).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from ingest_codex import call_codex, find_codex_cli  # noqa: E402
from metrics import DB_PATH, init_db  # noqa: E402


def parse_iso(ts: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp with Z or offset into a tz-aware UTC datetime."""
    if not ts:
        return None
    s = ts.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def load_bead_windows(project_path: Path) -> list[tuple[str, datetime, datetime, str]]:
    """Return [(bead_id, window_start, window_end, project_name)] for a project.

    - Closed beads with both started_at + closed_at form a closed window.
    - In-progress beads with started_at form a window ending at now (UTC).
    - Beads missing started_at are skipped (no claim timestamp => no window).
    """
    if not (project_path / ".beads").exists():
        return []

    results: list[tuple[str, datetime, datetime, str]] = []
    now = datetime.now(timezone.utc)
    project_name = project_path.name

    for status in ("closed", "in_progress"):
        try:
            proc = subprocess.run(  # noqa: S603,S607
                ["bd", "list", "--status", status, "--limit", "2000", "--json"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=60,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            print(f"backfill_codex: bd list failed for {project_path}: {exc}", file=sys.stderr)
            continue
        if proc.returncode != 0:
            print(
                f"backfill_codex: bd list exited {proc.returncode} in {project_path}: "
                f"{proc.stderr.strip()[:200]}",
                file=sys.stderr,
            )
            continue
        try:
            rows = json.loads(proc.stdout or "[]")
        except json.JSONDecodeError:
            continue

        for r in rows:
            start = parse_iso(r.get("started_at"))
            if not start:
                continue
            end = parse_iso(r.get("closed_at")) if status == "closed" else now
            if not end or end < start:
                continue
            results.append((r["id"], start, end, project_name))

    return results


def pick_narrowest(
    ts: datetime,
    windows: list[tuple[str, datetime, datetime, str]],
) -> tuple[str, str] | None:
    """Return (bead_id, project_name) for the narrowest window containing ts, or None."""
    candidates = [(bid, s, e, pn) for bid, s, e, pn in windows if s <= ts <= e]
    if not candidates:
        return None
    best = min(candidates, key=lambda w: (w[2] - w[1]).total_seconds())
    return (best[0], best[3])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Retroactively attribute Codex sessions to beads by time window."
    )
    parser.add_argument(
        "--projects",
        nargs="*",
        help="Project paths to load bead windows from. Default: cwd.",
    )
    parser.add_argument("--since", help="Start date (YYYYMMDD) for Codex sessions.")
    parser.add_argument("--until", help="End date (YYYYMMDD) for Codex sessions.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be upserted without touching metrics.db.",
    )
    parser.add_argument(
        "--warn-if-reasoning",
        action="store_true",
        help="Warn for rows that already have reasoning_tokens>0 (possible double-count).",
    )
    args = parser.parse_args()

    cmd = find_codex_cli()
    if cmd is None:
        print("backfill_codex: ccusage-codex not found — skipping", file=sys.stderr)
        return 1

    if not DB_PATH.exists():
        print(f"backfill_codex: metrics DB {DB_PATH} does not exist — skipping", file=sys.stderr)
        return 1

    project_paths = [Path(p).resolve() for p in (args.projects or [os.getcwd()])]
    missing = [p for p in project_paths if not (p / ".beads").exists()]
    if missing:
        for p in missing:
            print(f"backfill_codex: {p} has no .beads/ — skipping", file=sys.stderr)
    project_paths = [p for p in project_paths if (p / ".beads").exists()]
    if not project_paths:
        print("backfill_codex: no valid bead projects found", file=sys.stderr)
        return 1

    windows: list[tuple[str, datetime, datetime, str]] = []
    for p in project_paths:
        w = load_bead_windows(p)
        print(f"backfill_codex: {p.name}: {len(w)} beads with windows", file=sys.stderr)
        windows.extend(w)

    if not windows:
        print("backfill_codex: no bead windows — nothing to attribute", file=sys.stderr)
        return 0

    data = call_codex(cmd, args.since, args.until)
    if data is None:
        return 1
    sessions = data.get("sessions", [])
    print(f"backfill_codex: loaded {len(sessions)} Codex sessions", file=sys.stderr)

    # (bead_id, date_str) -> aggregated codex deltas
    agg: dict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: {
            "total": 0,
            "cost": 0.0,
            "cached": 0,
            "reasoning": 0,
            "session_count": 0,
        }
    )
    unattributed = 0
    unattributed_cost = 0.0
    project_hits: dict[str, int] = defaultdict(int)

    for s in sessions:
        ts = parse_iso(s.get("lastActivity"))
        if ts is None:
            unattributed += 1
            unattributed_cost += float(s.get("costUSD", 0.0))
            continue
        match = pick_narrowest(ts, windows)
        if match is None:
            unattributed += 1
            unattributed_cost += float(s.get("costUSD", 0.0))
            continue
        bead_id, proj_name = match
        date_str = ts.date().isoformat()
        key = (bead_id, date_str)
        agg[key]["total"] += int(s.get("totalTokens", 0))
        agg[key]["cost"] += float(s.get("costUSD", 0.0))
        agg[key]["cached"] += int(s.get("cachedInputTokens", 0))
        agg[key]["reasoning"] += int(s.get("reasoningOutputTokens", 0))
        agg[key]["session_count"] += 1
        project_hits[proj_name] += 1

    if not agg:
        print(
            f"backfill_codex: no Codex sessions matched any bead window "
            f"({unattributed} unattributed, ${unattributed_cost:.2f})",
            file=sys.stderr,
        )
        return 0

    conn = init_db(DB_PATH)
    updated = 0
    inserted = 0
    warned = 0

    try:
        for (bead_id, date_str), delta in sorted(agg.items()):
            cur = conn.execute(
                """
                SELECT id, total_tokens, cost_usd, cache_read_tokens,
                       cache_creation_tokens, reasoning_tokens
                FROM bead_runs WHERE bead_id = ? AND date = ?
                ORDER BY id DESC LIMIT 1
                """,
                (bead_id, date_str),
            )
            row = cur.fetchone()

            new_total = int(delta["total"])
            new_cost = delta["cost"]
            new_cached = int(delta["cached"])
            new_reasoning = int(delta["reasoning"])

            if row is not None:
                row_id, cur_total, cur_cost, cur_cache_r, cur_cache_c, cur_reason = row
                if args.warn_if_reasoning and cur_reason > 0:
                    print(
                        f"backfill_codex: WARN {bead_id}@{date_str} already has "
                        f"reasoning_tokens={cur_reason} (possible double-count)",
                        file=sys.stderr,
                    )
                    warned += 1
                merged_total = cur_total + new_total
                merged_cost = cur_cost + new_cost
                merged_cache_r = cur_cache_r + new_cached
                merged_reason = cur_reason + new_reasoning
                if args.dry_run:
                    print(
                        f"DRY-RUN UPDATE {bead_id}@{date_str}: "
                        f"+{new_total} tokens +${new_cost:.2f} "
                        f"+{new_reasoning} reasoning ({int(delta['session_count'])} sessions)"
                    )
                    continue
                conn.execute(
                    """
                    UPDATE bead_runs
                    SET total_tokens = ?, cost_usd = ?, cache_read_tokens = ?,
                        reasoning_tokens = ?
                    WHERE id = ?
                    """,
                    (merged_total, merged_cost, merged_cache_r, merged_reason, row_id),
                )
                updated += 1
            else:
                if args.dry_run:
                    print(
                        f"DRY-RUN INSERT {bead_id}@{date_str}: "
                        f"{new_total} tokens ${new_cost:.2f} "
                        f"{new_reasoning} reasoning ({int(delta['session_count'])} sessions)"
                    )
                    continue
                conn.execute(
                    """
                    INSERT INTO bead_runs (
                        bead_id, date, total_tokens, cost_usd,
                        cache_read_tokens, cache_creation_tokens, reasoning_tokens
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (bead_id, date_str, new_total, new_cost, new_cached, 0, new_reasoning),
                )
                inserted += 1
        if not args.dry_run:
            conn.commit()
    finally:
        conn.close()

    print(
        f"backfill_codex: {updated} updated, {inserted} inserted, "
        f"{unattributed} unattributed sessions (${unattributed_cost:.2f}), "
        f"{warned} warnings"
    )
    for proj, hits in sorted(project_hits.items()):
        print(f"  - {proj}: {hits} sessions attributed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
