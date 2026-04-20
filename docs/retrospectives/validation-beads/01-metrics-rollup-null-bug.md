---
title: "Metrics rollup null pointer on missing run_id"
description: >
  The rollup_run() function in beads-workflow/lib/orchestrator/metrics.py raises
  AttributeError when called on a BeadRun whose run_id is None (legacy row with
  no backfill). Fix: guard the rollup with an early-return if run_id is falsy,
  and add a test covering the None path.
type: bug
effort: micro
rubric_weight: 1
expected_complexity: trivial — one guard clause + one test
---

## Scenario

A developer runs `bd metrics rollup <bead_id>` against a bead created before the
`run_id` backfill migration (CCP-2vo.2). The DB row has `run_id = NULL`. The
`rollup_run()` helper executes a `WHERE run_id = ?` query with `None`, which
SQLite silently treats as `WHERE run_id IS NULL`, matching no rows and returning
an empty result set. A downstream assertion then raises `AttributeError: 'NoneType'
object has no attribute 'total_tokens'`.

## Acceptance Criteria

- `rollup_run(run_id=None)` returns `None` (or raises `ValueError`) instead of `AttributeError`
- Unit test `test_rollup_null_run_id` is green
- Existing rollup tests remain green
- No change to the DB schema or backfill logic

## MoC Table

| Metric | Before | After |
|--------|--------|-------|
| Unhandled exceptions on legacy rows | 1 per invocation | 0 |
| Test coverage for `rollup_run` | partial | null-path covered |

## Baseline Sketch

```python
# beads-workflow/lib/orchestrator/metrics.py — before
def rollup_run(run_id: str) -> BeadRun:
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM bead_runs WHERE run_id = ?", (run_id,)
    ).fetchone()
    return _row_to_beadrun(row)   # crashes if row is None

# after
def rollup_run(run_id: str | None) -> BeadRun | None:
    if not run_id:
        return None
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM bead_runs WHERE run_id = ?", (run_id,)
    ).fetchone()
    return _row_to_beadrun(row) if row else None
```
