#!/usr/bin/env python3
"""
Migration script: add run_id identity, rollup columns, and agent_calls table to metrics.db.

Idempotent — safe to run multiple times.
Usage: python3 migrate_metrics_run_id.py [--db-path PATH]
"""

import argparse
import sqlite3
import uuid
from pathlib import Path

DEFAULT_DB_PATH = Path.home() / ".claude" / "metrics.db"

NEW_BEAD_RUNS_COLUMNS = [
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

CREATE_AGENT_CALLS_SQL = """
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


def migrate(db_path: Path) -> None:
    if not db_path.exists():
        print(f"Database not found at {db_path} — nothing to migrate.")
        return

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(bead_runs)")}
        added_columns = []

        # Step 1+2: Add run_id column and backfill UUIDs
        if "run_id" not in existing_cols:
            conn.execute("ALTER TABLE bead_runs ADD COLUMN run_id TEXT")
            added_columns.append("run_id")
            print("Added column: run_id")

        rows_needing_uuid = conn.execute(
            "SELECT id FROM bead_runs WHERE run_id IS NULL OR run_id = ''"
        ).fetchall()
        backfilled = 0
        for row in rows_needing_uuid:
            conn.execute(
                "UPDATE bead_runs SET run_id = ? WHERE id = ?",
                (str(uuid.uuid4()), row["id"]),
            )
            backfilled += 1
        conn.commit()

        # Step 3: Create UNIQUE index on run_id
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_bead_runs_run_id ON bead_runs(run_id)"
        )

        # Step 4: Add mode and rollup columns if missing
        existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(bead_runs)")}
        for col_name, col_def in NEW_BEAD_RUNS_COLUMNS:
            if col_name not in existing_cols:
                conn.execute(f"ALTER TABLE bead_runs ADD COLUMN {col_name} {col_def}")
                added_columns.append(col_name)
                print(f"Added column: {col_name}")

        # Step 5: Backfill mode for rows where NULL or ''
        conn.execute(
            "UPDATE bead_runs SET mode = 'full-2pane' WHERE mode IS NULL OR mode = ''"
        )

        # Step 6: Create agent_calls table and indexes
        conn.execute(CREATE_AGENT_CALLS_SQL)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_calls_run ON agent_calls(run_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_calls_bead ON agent_calls(bead_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_calls_model ON agent_calls(model)"
        )

        conn.commit()

        total_rows = conn.execute("SELECT COUNT(*) FROM bead_runs").fetchone()[0]
        print(f"\nMigration summary:")
        print(f"  DB path:          {db_path}")
        print(f"  Total bead_runs:  {total_rows}")
        print(f"  UUIDs backfilled: {backfilled}")
        print(f"  Columns added:    {added_columns if added_columns else '(none — already up to date)'}")

    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate metrics.db schema (idempotent)")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to metrics.db (default: {DEFAULT_DB_PATH})",
    )
    args = parser.parse_args()
    migrate(args.db_path)


if __name__ == "__main__":
    main()
