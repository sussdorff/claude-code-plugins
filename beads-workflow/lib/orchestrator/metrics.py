"""
Bead Metrics — SQLite persistence for per-bead token cost tracking.
DB location: ~/.claude/metrics.db
Table: bead_runs
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

DB_PATH = Path.home() / ".claude" / "metrics.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS bead_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bead_id TEXT NOT NULL,
    date TEXT NOT NULL,
    impl_tokens INTEGER DEFAULT 0,
    impl_duration_ms INTEGER DEFAULT 0,
    review_iterations INTEGER DEFAULT 0,
    review_tokens INTEGER DEFAULT 0,
    verification_tokens INTEGER DEFAULT 0,
    uat_tokens INTEGER DEFAULT 0,
    constraint_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    quality_grade TEXT DEFAULT '',
    tdd_grade TEXT DEFAULT '',
    ak_count INTEGER DEFAULT 0
)
"""

_USAGE_RE = re.compile(r"<usage>(.*?)</usage>", re.DOTALL)

_EMPTY_USAGE: dict[str, int] = {
    "total_tokens": 0,
    "input_tokens": 0,
    "output_tokens": 0,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "duration_ms": 0,
}


@dataclass
class BeadRun:
    bead_id: str
    date: str = field(default_factory=lambda: str(date.today()))
    impl_tokens: int = 0
    impl_duration_ms: int = 0
    review_iterations: int = 0
    review_tokens: int = 0
    verification_tokens: int = 0
    uat_tokens: int = 0
    constraint_tokens: int = 0
    total_tokens: int = 0
    quality_grade: str = ""
    tdd_grade: str = ""
    ak_count: int = 0


def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Initialize DB and ensure bead_runs table exists. Returns connection."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    return conn


def parse_usage(text: str) -> dict[str, int]:
    """
    Parse <usage> block from subagent response.

    Expected format:
    <usage>{"input_tokens": N, "output_tokens": M, "cache_creation_input_tokens": X, "cache_read_input_tokens": Y}</usage>

    Total tokens = input_tokens + output_tokens + cache_creation_input_tokens + cache_read_input_tokens.

    Returns dict with token keys; all default to 0 if absent.
    """
    match = _USAGE_RE.search(text)
    if not match:
        return dict(_EMPTY_USAGE)

    try:
        data: dict[str, int] = json.loads(match.group(1).strip())
    except (json.JSONDecodeError, ValueError):
        return dict(_EMPTY_USAGE)

    input_tokens = data.get("input_tokens", 0)
    output_tokens = data.get("output_tokens", 0)
    cache_creation = data.get("cache_creation_input_tokens", 0)
    cache_read = data.get("cache_read_input_tokens", 0)
    duration_ms = data.get("duration_ms", 0)
    total = input_tokens + output_tokens + cache_creation + cache_read

    return {
        "total_tokens": total,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_creation_input_tokens": cache_creation,
        "cache_read_input_tokens": cache_read,
        "duration_ms": duration_ms,
    }


def insert_bead_run(conn: sqlite3.Connection, run: BeadRun) -> None:
    """Insert a BeadRun row into bead_runs. Commits after insert."""
    conn.execute(
        """
        INSERT INTO bead_runs (
            bead_id, date, impl_tokens, impl_duration_ms, review_iterations,
            review_tokens, verification_tokens, uat_tokens, constraint_tokens,
            total_tokens, quality_grade, tdd_grade, ak_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run.bead_id,
            run.date,
            run.impl_tokens,
            run.impl_duration_ms,
            run.review_iterations,
            run.review_tokens,
            run.verification_tokens,
            run.uat_tokens,
            run.constraint_tokens,
            run.total_tokens,
            run.quality_grade,
            run.tdd_grade,
            run.ak_count,
        ),
    )
    conn.commit()


def query_report(
    top: int | None = None,
    bead_id: str | None = None,
    db_path: Path = DB_PATH,
) -> str:
    """
    Query ~/.claude/metrics.db and return a formatted cost report.

    Args:
        top: Limit to top N most expensive beads.
        bead_id: Show details for a single bead only.
        db_path: Override DB path (mainly for testing).

    Returns:
        Formatted markdown string.
    """
    if not db_path.exists():
        return "No data yet — implement some beads first."

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        # Single-bead detail view
        if bead_id is not None:
            rows = conn.execute(
                "SELECT * FROM bead_runs WHERE bead_id=? ORDER BY date DESC",
                (bead_id,),
            ).fetchall()
            if not rows:
                return "No data yet — implement some beads first."
            lines = [f"## Bead Token Cost Report — {bead_id}\n"]
            lines.append(_render_table(rows))
            return "\n".join(lines)

        # Full report / top-N
        all_rows = conn.execute(
            "SELECT * FROM bead_runs ORDER BY total_tokens DESC"
        ).fetchall()
    finally:
        conn.close()

    if not all_rows:
        return "No data yet — implement some beads first."

    total_beads = len(all_rows)
    grand_total = sum(r["total_tokens"] for r in all_rows)
    avg_tokens = grand_total // total_beads if total_beads else 0

    # impl:review ratio stats
    ratios = []
    for r in all_rows:
        if r["review_tokens"] > 0:
            ratios.append(r["impl_tokens"] / r["review_tokens"])

    avg_ratio_str = f"{sum(ratios)/len(ratios):.1f}:1" if ratios else "N/A"

    # Ratio distribution
    heavy = sum(1 for r in ratios if r < 1)
    balanced = sum(1 for r in ratios if 1 <= r <= 3)
    clean = sum(1 for r in ratios if r > 3)

    # Weekly trend
    weeks: dict[str, list[int]] = {}
    for r in all_rows:
        try:
            d = datetime.strptime(r["date"], "%Y-%m-%d")
            week_key = d.strftime("%G-W%V")
            weeks.setdefault(week_key, []).append(r["total_tokens"])
        except (ValueError, TypeError):
            pass

    display_rows = all_rows[:top] if top is not None else all_rows

    lines = [
        "## Bead Token Cost Report\n",
        "### Summary",
        f"Total beads tracked: {total_beads}",
        f"Total tokens consumed: {grand_total:,}",
        f"Avg tokens per bead: {avg_tokens:,}",
        f"Avg impl:review ratio: {avg_ratio_str}",
        "",
        "### Most Expensive Beads",
        _render_table(display_rows),
        "",
        "### Impl:Review Ratio Distribution",
        f"< 1:1  (review-heavy): {heavy} beads — impl was messy",
        f"1-3:1  (balanced):     {balanced} beads",
        f"> 3:1  (clean impl):   {clean} beads",
    ]

    if weeks:
        lines += [
            "",
            "### Weekly Trend",
            "| Week | Beads | Avg Tokens |",
            "|------|-------|-----------|",
        ]
        for week, tokens in sorted(weeks.items()):
            avg = sum(tokens) // len(tokens)
            lines.append(f"| {week} | {len(tokens)} | {avg:,} |")

    return "\n".join(lines)


def _render_table(rows: list[sqlite3.Row]) -> str:
    """Render a markdown table of bead_runs rows."""
    header = "| Bead | Date | Impl | Review (N iter) | Verify | Total | Ratio |"
    sep = "|------|------|------|----------------|--------|-------|-------|"
    table_rows = []
    for r in rows:
        ratio = (
            f"{r['impl_tokens'] / r['review_tokens']:.1f}:1"
            if r["review_tokens"] > 0
            else "N/A"
        )
        table_rows.append(
            f"| {r['bead_id']} | {r['date']} "
            f"| {r['impl_tokens']:,} "
            f"| {r['review_tokens']:,} ({r['review_iterations']}x) "
            f"| {r['verification_tokens']:,} "
            f"| {r['total_tokens']:,} "
            f"| {ratio} |"
        )
    return "\n".join([header, sep] + table_rows)
