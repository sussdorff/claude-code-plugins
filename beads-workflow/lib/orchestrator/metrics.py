"""
Bead Metrics — SQLite persistence for per-bead token cost tracking.
DB location: ~/.claude/metrics.db
Tables: bead_runs, agent_calls
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import sys
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

logger = logging.getLogger("metrics")

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
    # CCP-2vo.2: run identity, mode, and rollup columns
    ("mode", "TEXT DEFAULT 'full-2pane'"),
    ("codex_total_tokens", "INTEGER DEFAULT 0"),
    ("codex_runs", "INTEGER DEFAULT 0"),
    ("fix_agent_tokens", "INTEGER DEFAULT 0"),
    ("fix_agent_invocations", "INTEGER DEFAULT 0"),
    ("auto_decisions", "INTEGER DEFAULT 0"),
    ("deviations_from_reco", "INTEGER DEFAULT 0"),
    ("session_close_tokens", "INTEGER DEFAULT 0"),
    ("session_close_duration_ms", "INTEGER DEFAULT 0"),
]

_CREATE_AGENT_CALLS_SQL = """
CREATE TABLE IF NOT EXISTS agent_calls (
  id                       INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id                   TEXT NOT NULL,
  bead_id                  TEXT NOT NULL,
  wave_id                  TEXT,
  phase_label              TEXT NOT NULL,
  agent_label              TEXT NOT NULL,
  model                    TEXT NOT NULL,
  iteration                INTEGER DEFAULT 1,
  input_tokens             INTEGER DEFAULT 0,
  cached_input_tokens      INTEGER DEFAULT 0,
  output_tokens            INTEGER DEFAULT 0,
  reasoning_output_tokens  INTEGER DEFAULT 0,
  total_tokens             INTEGER DEFAULT 0,
  duration_ms              INTEGER DEFAULT 0,
  exit_code                INTEGER DEFAULT 0,
  recorded_at              TEXT NOT NULL,
  FOREIGN KEY (run_id) REFERENCES bead_runs(run_id)
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
    wave_id: str = ""
    model_impl: str = ""
    model_review: str = ""
    phase2_triggered: int = 0
    phase2_findings: int = 0
    phase2_critical: int = 0
    run_id: str = ""


def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Initialize DB and ensure bead_runs and agent_calls tables exist. Migrates schema if needed."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(CREATE_TABLE_SQL)
    # Migrate existing tables: add new columns if missing
    existing = {row[1] for row in conn.execute("PRAGMA table_info(bead_runs)")}
    for col_name, col_def in _MIGRATE_COLUMNS:
        if col_name not in existing:
            conn.execute(f"ALTER TABLE bead_runs ADD COLUMN {col_name} {col_def}")

    # CCP-2vo.2: run_id identity — add column, backfill UUIDs, create unique index
    existing = {row[1] for row in conn.execute("PRAGMA table_info(bead_runs)")}
    if "run_id" not in existing:
        conn.execute("ALTER TABLE bead_runs ADD COLUMN run_id TEXT")
    rows_needing_uuid = conn.execute(
        "SELECT id FROM bead_runs WHERE run_id IS NULL OR run_id = ''"
    ).fetchall()
    for row in rows_needing_uuid:
        conn.execute(
            "UPDATE bead_runs SET run_id = ? WHERE id = ?",
            (str(uuid.uuid4()), row[0]),
        )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_bead_runs_run_id ON bead_runs(run_id)"
    )

    # CCP-2vo.2: agent_calls child table
    conn.execute(_CREATE_AGENT_CALLS_SQL)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_calls_run ON agent_calls(run_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_calls_bead ON agent_calls(bead_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_calls_model ON agent_calls(model)")

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
    """Insert a BeadRun row into bead_runs. Commits after insert.

    Automatically generates and populates run_id (UUID4) if the BeadRun
    does not already have one set.
    """
    if not run.run_id:
        run.run_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO bead_runs (
            bead_id, date, impl_tokens, impl_duration_ms, review_iterations,
            review_tokens, verification_tokens, uat_tokens, constraint_tokens,
            total_tokens, quality_grade, tdd_grade, ak_count,
            wave_id, model_impl, model_review,
            phase2_triggered, phase2_findings, phase2_critical,
            run_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            run.run_id,
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
    run_id: str | None = None,
    db_path: Path = DB_PATH,
) -> str:
    """
    UPSERT ccusage-sourced token + cost data for a bead_runs row.

    When run_id is provided, the target row is looked up by run_id directly
    (WHERE run_id = ?), preventing cross-contamination between multiple same-day
    runs of the same bead.

    When run_id is absent (backward-compat for old callers), falls back to the
    previous (bead_id, date) lookup — most recent matching row in place if
    present; otherwise inserts a new row. If the found row has no run_id, one
    is generated and written back to maintain identity going forward.

    Returns: 'updated' or 'inserted'.
    """
    conn = init_db(db_path)
    try:
        if run_id is not None:
            # New model: look up by run_id for precise isolation
            cur = conn.execute(
                "SELECT id FROM bead_runs WHERE run_id = ?",
                (run_id,),
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
                    WHERE run_id = ?
                    """,
                    (
                        total_tokens,
                        cost_usd,
                        cache_read_tokens,
                        cache_creation_tokens,
                        reasoning_tokens,
                        run_id,
                    ),
                )
                conn.commit()
                return "updated"
            # run_id was provided but row not found — insert with that run_id
            conn.execute(
                """
                INSERT INTO bead_runs (
                    bead_id, date, total_tokens, cost_usd,
                    cache_read_tokens, cache_creation_tokens, reasoning_tokens,
                    run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    bead_id,
                    date_str,
                    total_tokens,
                    cost_usd,
                    cache_read_tokens,
                    cache_creation_tokens,
                    reasoning_tokens,
                    run_id,
                ),
            )
            conn.commit()
            return "inserted"

        # Backward-compat path: look up by (bead_id, date)
        cur = conn.execute(
            """
            SELECT id, run_id FROM bead_runs
            WHERE bead_id = ? AND date = ?
            ORDER BY id DESC LIMIT 1
            """,
            (bead_id, date_str),
        )
        row = cur.fetchone()
        if row is not None:
            existing_run_id = row[1]
            # Backfill run_id if missing on the found row
            if not existing_run_id:
                existing_run_id = str(uuid.uuid4())
                conn.execute(
                    "UPDATE bead_runs SET run_id = ? WHERE id = ?",
                    (existing_run_id, row[0]),
                )
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
                cache_read_tokens, cache_creation_tokens, reasoning_tokens,
                run_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bead_id,
                date_str,
                total_tokens,
                cost_usd,
                cache_read_tokens,
                cache_creation_tokens,
                reasoning_tokens,
                str(uuid.uuid4()),
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
    run_id: str | None = None,
    db_path: Path = DB_PATH,
) -> None:
    """Update phase2 columns on a bead_runs row.

    When run_id is provided, targets that specific run (WHERE run_id = ?),
    preventing a delayed phase2 update from writing to the wrong run when
    multiple runs exist for the same bead.

    When run_id is absent (backward-compat for old callers), falls back to
    updating the most recent row for the given bead_id.
    """
    if not db_path.exists():
        return
    conn = sqlite3.connect(str(db_path))
    try:
        if run_id is not None:
            conn.execute(
                """
                UPDATE bead_runs
                SET phase2_triggered = ?, phase2_findings = ?, phase2_critical = ?
                WHERE run_id = ?
                """,
                (int(triggered), findings, critical, run_id),
            )
        else:
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


# ---------------------------------------------------------------------------
# CCP-2vo.2: Run identity + agent_calls public API
# These four functions form the stable public contract for CCP-2vo.3, CCP-2vo.4, CCP-2vo.8.
# ---------------------------------------------------------------------------


def start_run(
    bead_id: str,
    wave_id: str | None = None,
    mode: str = "full-1pane",
    db_path: Path = DB_PATH,
) -> str:
    """
    Create a new bead_runs row and return its run_id.

    Run identity model: each call to start_run creates one logical run of a bead.
    Multiple runs of the same bead_id are valid (retries, replays, A/B validation).
    The returned run_id is a UUID4 string and is the authoritative key for
    insert_agent_call(), rollup_run(), and get_run().
    """
    run_id = str(uuid.uuid4())
    today = str(date.today())
    conn = init_db(db_path)
    try:
        conn.execute(
            """
            INSERT INTO bead_runs (bead_id, date, wave_id, mode, run_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (bead_id, today, wave_id or "", mode, run_id),
        )
        conn.commit()
    finally:
        conn.close()
    return run_id


def insert_agent_call(
    run_id: str,
    bead_id: str,
    phase_label: str,
    agent_label: str,
    model: str,
    iteration: int,
    input_tokens: int,
    cached_input_tokens: int,
    output_tokens: int,
    reasoning_output_tokens: int,
    total_tokens: int,
    duration_ms: int,
    exit_code: int,
    wave_id: str | None = None,
    db_path: Path = DB_PATH,
) -> int:
    """
    Insert one row into agent_calls. Returns the new row id.

    Raises ValueError if run_id is not present in bead_runs (FK integrity check
    done in Python since SQLite FK enforcement is optional).
    """
    conn = init_db(db_path)
    try:
        existing = conn.execute(
            "SELECT id FROM bead_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if existing is None:
            raise ValueError(f"run_id '{run_id}' not found in bead_runs")

        recorded_at = datetime.now(timezone.utc).isoformat()
        cur = conn.execute(
            """
            INSERT INTO agent_calls (
                run_id, bead_id, wave_id, phase_label, agent_label, model,
                iteration, input_tokens, cached_input_tokens, output_tokens,
                reasoning_output_tokens, total_tokens, duration_ms, exit_code,
                recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                bead_id,
                wave_id,
                phase_label,
                agent_label,
                model,
                iteration,
                input_tokens,
                cached_input_tokens,
                output_tokens,
                reasoning_output_tokens,
                total_tokens,
                duration_ms,
                exit_code,
                recorded_at,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def rollup_run(run_id: str, db_path: Path = DB_PATH) -> None:
    """
    Aggregate agent_calls for this run_id and update bead_runs rollup columns:
    - codex_total_tokens = SUM(total_tokens) WHERE model LIKE '%codex%' OR '%o1%' OR '%o3%'
    - codex_runs = COUNT(*) with same filter
    - fix_agent_tokens = SUM(total_tokens) WHERE phase_label LIKE '%fix%'
    - fix_agent_invocations = COUNT(*) WHERE phase_label LIKE '%fix%'
    - session_close_tokens = SUM(total_tokens) WHERE phase_label LIKE '%session%close%'
    - session_close_duration_ms = SUM(duration_ms) WHERE phase_label LIKE '%session%close%'

    Raises ValueError if run_id is None or an empty string. Binding None into
    the WHERE clause would silently match nothing (SQLite treats `run_id = NULL`
    as always-false) and drop the caller's work invisibly — which violates the
    CCP-imb acceptance criteria. Callers that may see unattributed work should
    check `run_id` up front rather than relying on silent best-effort rollup.
    """
    if not run_id:
        raise ValueError(
            "rollup_run() requires a non-empty run_id; received "
            f"{run_id!r}. Unattributed agent_calls cannot be aggregated "
            "silently — set run_id on the caller or inspect orphan rows "
            "directly."
        )

    conn = init_db(db_path)
    try:
        # Surface orphan agent_calls (run_id IS NULL) so they are not silently
        # dropped. These can exist on databases upgraded from a pre-CCP-2vo.2
        # schema where agent_calls.run_id was nullable. We do not attempt to
        # re-attribute them — just make them visible in the operator's log so
        # the gap is noticed and can be fixed at the caller site. Out-of-scope
        # per CCP-imb: modifying the agent_calls schema.
        orphan_row = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(total_tokens), 0) "
            "FROM agent_calls WHERE run_id IS NULL OR run_id = ''"
        ).fetchone()
        orphan_count = orphan_row[0] if orphan_row else 0
        if orphan_count:
            logger.warning(
                "rollup_run: %d orphan agent_calls row(s) with NULL run_id "
                "detected (total_tokens=%d); excluded from rollup for run_id=%s",
                orphan_count,
                orphan_row[1],
                run_id,
            )

        def agg(query: str, params: tuple) -> int:
            result = conn.execute(query, params).fetchone()
            return result[0] or 0

        codex_filter = (
            "run_id = ? AND (model LIKE '%codex%' OR model LIKE '%o1%' OR model LIKE '%o3%')"
        )
        codex_total_tokens = agg(
            f"SELECT SUM(total_tokens) FROM agent_calls WHERE {codex_filter}", (run_id,)
        )
        codex_runs = agg(
            f"SELECT COUNT(*) FROM agent_calls WHERE {codex_filter}", (run_id,)
        )

        fix_filter = "run_id = ? AND phase_label LIKE '%fix%'"
        fix_agent_tokens = agg(
            f"SELECT SUM(total_tokens) FROM agent_calls WHERE {fix_filter}", (run_id,)
        )
        fix_agent_invocations = agg(
            f"SELECT COUNT(*) FROM agent_calls WHERE {fix_filter}", (run_id,)
        )

        sc_filter = "run_id = ? AND phase_label LIKE '%session%close%'"
        session_close_tokens = agg(
            f"SELECT SUM(total_tokens) FROM agent_calls WHERE {sc_filter}", (run_id,)
        )
        session_close_duration_ms = agg(
            f"SELECT SUM(duration_ms) FROM agent_calls WHERE {sc_filter}", (run_id,)
        )

        conn.execute(
            """
            UPDATE bead_runs SET
                codex_total_tokens = ?,
                codex_runs = ?,
                fix_agent_tokens = ?,
                fix_agent_invocations = ?,
                session_close_tokens = ?,
                session_close_duration_ms = ?
            WHERE run_id = ?
            """,
            (
                codex_total_tokens,
                codex_runs,
                fix_agent_tokens,
                fix_agent_invocations,
                session_close_tokens,
                session_close_duration_ms,
                run_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_run(run_id: str, db_path: Path = DB_PATH) -> dict:
    """
    Fetch a bead_runs row by run_id. Returns a dict of all columns.
    Raises KeyError if run_id not found.
    """
    conn = init_db(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM bead_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        raise KeyError(f"run_id '{run_id}' not found in bead_runs")
    return dict(row)
