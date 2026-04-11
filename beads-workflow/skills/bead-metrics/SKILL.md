---
name: bead-metrics
model: sonnet
description: >-
  Query per-bead token cost metrics from ~/.claude/metrics.db.
  Shows cost table, impl:review ratios, most expensive beads, cost trend over time.
  Triggers on: bead metrics, token cost report, bead costs, /bead-metrics.
---

# Bead Metrics Report

Query `~/.claude/metrics.db` and output a formatted cost report.

## Arguments

- *(empty)* — Full report (all beads)
- `--top=N` — Show only top N most expensive beads (default: all)
- `--bead=<id>` — Show single bead details

## Workflow

Parse arguments from `{ARGS}`:
- If `--top=N` present, extract N as integer and pass as `top=N`
- If `--bead=<id>` present, extract id and pass as `bead_id="<id>"`
- Otherwise pass no arguments (full report)

Run the query script:

```bash
uv run python -c "
import sys
sys.path.insert(0, '/Users/malte/code/claude')
from orchestrator.metrics import query_report
# Replace with actual parsed args:
# e.g. print(query_report(top=5))
# e.g. print(query_report(bead_id='claude-i7it'))
print(query_report())
"
```

### Argument Examples

Full report:
```bash
uv run python -c "
import sys; sys.path.insert(0, '/Users/malte/code/claude')
from orchestrator.metrics import query_report
print(query_report())
"
```

Top 5 most expensive:
```bash
uv run python -c "
import sys; sys.path.insert(0, '/Users/malte/code/claude')
from orchestrator.metrics import query_report
print(query_report(top=5))
"
```

Single bead detail:
```bash
uv run python -c "
import sys; sys.path.insert(0, '/Users/malte/code/claude')
from orchestrator.metrics import query_report
print(query_report(bead_id='claude-i7it'))
"
```

### Output Format

#### Empty DB
```
No data yet — implement some beads first.
```

#### Normal Report
```
## Bead Token Cost Report

### Summary
Total beads tracked: 12
Total tokens consumed: 4,231,088
Avg tokens per bead: 352,590
Avg impl:review ratio: 2.8:1

### Most Expensive Beads
| Bead | Date | Impl | Review (N iter) | Verify | Total | Ratio |
|------|------|------|----------------|--------|-------|-------|
| claude-i7it | 2026-04-05 | 81,079 | 92,007 (3x) | 30,517 | 235,244 | 0.9:1 |

### Impl:Review Ratio Distribution
< 1:1  (review-heavy): 2 beads — impl was messy
1-3:1  (balanced):     7 beads
> 3:1  (clean impl):   3 beads

### Weekly Trend
| Week | Beads | Avg Tokens |
|------|-------|-----------|
| 2026-W14 | 3 | 287,000 |
```

## Error Handling

If the script fails (import error, DB locked), report the error message and suggest running:
```bash
uv run pytest tests/orchestrator/test_metrics.py -v
```
to verify the metrics module is healthy.
