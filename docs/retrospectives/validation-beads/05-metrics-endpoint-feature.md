---
title: "Add /metrics/summary REST endpoint to beads metrics server"
description: >
  The beads metrics server currently exposes raw per-run data but has no
  aggregation endpoint. Add a GET /metrics/summary endpoint that returns
  totals and averages (total_tokens, mean_wall_clock_s, p50/p95 wall-clock,
  bead_count) over a configurable time window (default: last 30 days).
type: feature
effort: medium
rubric_weight: 3
expected_complexity: new endpoint + aggregation query + JSON schema + integration test
---

## Scenario

A developer wants to display a dashboard card showing "last 30 days: N beads,
avg X tokens, p95 wall-clock Y s". Currently they must query raw rows and
aggregate client-side. A /metrics/summary endpoint encapsulates the SQL and
returns a clean JSON payload.

## Acceptance Criteria

- `GET /metrics/summary?days=<N>` (default N=30) returns HTTP 200 with JSON:
  ```json
  {
    "window_days": 30,
    "bead_count": 42,
    "total_tokens": 1234567,
    "mean_tokens": 29394,
    "mean_wall_clock_s": 183.4,
    "p50_wall_clock_s": 152.1,
    "p95_wall_clock_s": 410.7
  }
  ```
- `days` parameter accepts 1–365; values outside range return HTTP 400 with
  `{"error": "days must be between 1 and 365"}`
- Integration test covers: default window, custom window, empty window (0 beads)
- OpenAPI spec (if present) updated with new route
- No changes to existing endpoints

## MoC Table

| Metric | Before | After |
|--------|--------|-------|
| Client-side aggregation calls | required | not required |
| REST endpoints | existing set | existing + /metrics/summary |
| P95 wall-clock visible in API | no | yes |

## Baseline Sketch

```python
# beads-workflow/lib/orchestrator/server.py (new route)
@app.get("/metrics/summary")
def metrics_summary(days: int = 30):
    if not 1 <= days <= 365:
        raise HTTPException(400, "days must be between 1 and 365")
    since = datetime.utcnow() - timedelta(days=days)
    rows = db.execute(
        """
        SELECT
            COUNT(*)               AS bead_count,
            SUM(total_tokens)      AS total_tokens,
            AVG(total_tokens)      AS mean_tokens,
            AVG(wall_clock_s)      AS mean_wall_clock_s,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY wall_clock_s) AS p50,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY wall_clock_s) AS p95
        FROM bead_runs
        WHERE started_at >= ?
        """,
        (since.isoformat(),),
    ).fetchone()
    return {
        "window_days": days,
        "bead_count": rows["bead_count"] or 0,
        "total_tokens": rows["total_tokens"] or 0,
        "mean_tokens": round(rows["mean_tokens"] or 0, 1),
        "mean_wall_clock_s": round(rows["mean_wall_clock_s"] or 0, 1),
        "p50_wall_clock_s": round(rows["p50"] or 0, 1),
        "p95_wall_clock_s": round(rows["p95"] or 0, 1),
    }
```
