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
    ak_count INTEGER DEFAULT 0,
    wave_id TEXT DEFAULT '',
    model_impl TEXT DEFAULT '',
    model_review TEXT DEFAULT '',
    phase2_triggered INTEGER DEFAULT 0,
    phase2_findings INTEGER DEFAULT 0,
    phase2_critical INTEGER DEFAULT 0
)
"""

# Migration: add new columns to existing databases that lack them.
_MIGRATE_COLUMNS = [
    ("wave_id", "TEXT DEFAULT ''"),
    ("model_impl", "TEXT DEFAULT ''"),
    ("model_review", "TEXT DEFAULT ''"),
    ("phase2_triggered", "INTEGER DEFAULT 0"),
    ("phase2_findings", "INTEGER DEFAULT 0"),
    ("phase2_critical", "INTEGER DEFAULT 0"),
    # CCP-d7b: ccusage-sourced fields (tokens from Claude Code JSONL / Codex JSONL
    # via the ccusage and @ccusage/codex CLI tools). Populated post-bead-close by
    # ingest_ccusage.py and ingest_codex.py; the orchestrator no longer touches them.
    ("cache_read_tokens", "INTEGER DEFAULT 0"),
    ("cache_creation_tokens", "INTEGER DEFAULT 0"),
    ("reasoning_tokens", "INTEGER DEFAULT 0"),
    ("cost_usd", "REAL DEFAULT 0.0"),
]

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
    wave_id: str = ""
    model_impl: str = ""
    model_review: str = ""
    phase2_triggered: int = 0
    phase2_findings: int = 0
    phase2_critical: int = 0


def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Initialize DB and ensure bead_runs table exists. Migrates schema if needed."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(CREATE_TABLE_SQL)
    # Migrate existing tables: add new columns if missing
    existing = {row[1] for row in conn.execute("PRAGMA table_info(bead_runs)")}
    for col_name, col_def in _MIGRATE_COLUMNS:
        if col_name not in existing:
            conn.execute(f"ALTER TABLE bead_runs ADD COLUMN {col_name} {col_def}")
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
            total_tokens, quality_grade, tdd_grade, ak_count,
            wave_id, model_impl, model_review,
            phase2_triggered, phase2_findings, phase2_critical
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            run.wave_id,
            run.model_impl,
            run.model_review,
            run.phase2_triggered,
            run.phase2_findings,
            run.phase2_critical,
        ),
    )
    conn.commit()


def upsert_ccusage_row(
    bead_id: str,
    date_str: str,
    total_tokens: int,
    cost_usd: float,
    cache_read_tokens: int,
    cache_creation_tokens: int,
    reasoning_tokens: int = 0,
    db_path: Path = DB_PATH,
) -> str:
    """
    UPSERT ccusage-sourced token + cost data for a (bead_id, date) row.

    Updates the most recent matching row in place if present; otherwise inserts a
    new row with only the ccusage-sourced fields populated (orchestrator-authored
    fields like quality_grade, wave_id stay at defaults).

    Returns: 'updated' or 'inserted'.
    """
    conn = init_db(db_path)
    try:
        cur = conn.execute(
            """
            SELECT id FROM bead_runs
            WHERE bead_id = ? AND date = ?
            ORDER BY id DESC LIMIT 1
            """,
            (bead_id, date_str),
        )
        row = cur.fetchone()
        if row is not None:
            conn.execute(
                """
                UPDATE bead_runs
                SET total_tokens = ?,
                    cost_usd = ?,
                    cache_read_tokens = ?,
                    cache_creation_tokens = ?,
                    reasoning_tokens = ?
                WHERE id = ?
                """,
                (
                    total_tokens,
                    cost_usd,
                    cache_read_tokens,
                    cache_creation_tokens,
                    reasoning_tokens,
                    row[0],
                ),
            )
            conn.commit()
            return "updated"

        conn.execute(
            """
            INSERT INTO bead_runs (
                bead_id, date, total_tokens, cost_usd,
                cache_read_tokens, cache_creation_tokens, reasoning_tokens
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bead_id,
                date_str,
                total_tokens,
                cost_usd,
                cache_read_tokens,
                cache_creation_tokens,
                reasoning_tokens,
            ),
        )
        conn.commit()
        return "inserted"
    finally:
        conn.close()


def update_verification_tokens(
    bead_id: str,
    tokens: int,
    db_path: Path = DB_PATH,
) -> None:
    """Update verification_tokens on the most recent row for a bead.

    Called by the orchestrator after Phase 4 completes, to persist
    the verification-agent's token cost. Uses <usage> block parsing
    rather than ccusage (which only gives session-level totals).
    """
    import sys

    if not db_path.exists():
        return
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.execute(
            """
            UPDATE bead_runs
            SET verification_tokens = ?
            WHERE id = (
                SELECT id FROM bead_runs WHERE bead_id = ? ORDER BY id DESC LIMIT 1
            )
            """,
            (tokens, bead_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            print(
                f"update_verification_tokens: no row found for bead_id={bead_id!r} — "
                "ensure insert_bead_run was called first",
                file=sys.stderr,
            )
    finally:
        conn.close()


def update_phase2_metrics(
    bead_id: str,
    triggered: bool,
    findings: int,
    critical: int,
    db_path: Path = DB_PATH,
) -> None:
    """Update phase2 columns on the most recent row for a bead."""
    if not db_path.exists():
        return
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """
            UPDATE bead_runs
            SET phase2_triggered = ?, phase2_findings = ?, phase2_critical = ?
            WHERE id = (
                SELECT id FROM bead_runs WHERE bead_id = ? ORDER BY id DESC LIMIT 1
            )
            """,
            (int(triggered), findings, critical, bead_id),
        )
        conn.commit()
    finally:
        conn.close()


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
    header = "| Bead | Date | Impl | Review (N iter) | Verify | Total | Ratio | Models | P2 |"
    sep = "|------|------|------|----------------|--------|-------|-------|--------|-----|"
    table_rows = []
    for r in rows:
        ratio = (
            f"{r['impl_tokens'] / r['review_tokens']:.1f}:1"
            if r["review_tokens"] > 0
            else "N/A"
        )
        model_impl = r["model_impl"] if r["model_impl"] else "-"
        model_review = r["model_review"] if r["model_review"] else "-"
        models = f"{model_impl}/{model_review}"
        p2 = f"{r['phase2_critical']}C/{r['phase2_findings']}F" if r["phase2_triggered"] else "-"
        table_rows.append(
            f"| {r['bead_id']} | {r['date']} "
            f"| {r['impl_tokens']:,} "
            f"| {r['review_tokens']:,} ({r['review_iterations']}x) "
            f"| {r['verification_tokens']:,} "
            f"| {r['total_tokens']:,} "
            f"| {ratio} "
            f"| {models} "
            f"| {p2} |"
        )
    return "\n".join([header, sep] + table_rows)


def query_wave_report(wave_id: str, db_path: Path = DB_PATH) -> str:
    """Query metrics for a specific wave and return a formatted report."""
    if not db_path.exists():
        return "No data yet."

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM bead_runs WHERE wave_id=? ORDER BY date DESC",
            (wave_id,),
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return f"No data for wave '{wave_id}'."

    total_tokens = sum(r["total_tokens"] for r in rows)
    p2_triggered = sum(1 for r in rows if r["phase2_triggered"])
    p2_critical = sum(r["phase2_critical"] for r in rows)
    p2_findings = sum(r["phase2_findings"] for r in rows)

    lines = [
        f"## Wave Report: {wave_id}\n",
        f"Beads: {len(rows)}",
        f"Total tokens: {total_tokens:,}",
        f"Phase 2 triggered: {p2_triggered}/{len(rows)} beads",
        f"Phase 2 findings: {p2_findings} total, {p2_critical} CRITICAL",
        "",
        _render_table(rows),
    ]
    return "\n".join(lines)
