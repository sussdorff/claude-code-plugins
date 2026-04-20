---
title: "Add wave-level summary card to bead-metrics TUI"
description: >
  The bead-metrics TUI (beads-workflow:bead-metrics skill) shows per-bead rows
  but has no wave-level aggregate card. Add a collapsible summary card at the
  top of the wave view that shows: wave_id, bead_count, total_tokens, mean
  wall-clock, and % beads in each status (done/in-progress/blocked).
type: feature
effort: medium
rubric_weight: 3
expected_complexity: new UI component + aggregation query + snapshot test
---

## Scenario

A tech lead reviews a completed wave in the TUI and wants a quick health
summary before drilling into individual beads. The new wave-summary card
answers "how did this wave go?" in 5 seconds without scrolling through all rows.

## Acceptance Criteria

- The wave view renders a summary card (first 4 lines) when `wave_id` is set:
  ```
  Wave  CCP-2vo  |  6 beads  |  total: 1.2M tokens  |  mean: 3m 04s
  Status: 4 done  1 in-progress  1 blocked
  ──────────────────────────────────────────────────────────────────
  ```
- Card is hidden when no `wave_id` is in scope (backward compatible)
- `% blocked` threshold > 33% highlights the blocked count in yellow
- Snapshot test (pytest + capsys or rich test runner) covers: all-done wave,
  mixed wave, and empty wave
- No changes to per-bead row rendering

## MoC Table

| Metric | Before | After |
|--------|--------|-------|
| Time to wave health overview | manual scroll | ~0s (card) |
| Wave-level token total visible | no | yes |
| Blocked-bead alert | none | yellow highlight > 33% |

## Baseline Sketch

```python
# beads-workflow/skills/bead-metrics/scripts/tui.py

def render_wave_card(wave_id: str, beads: list[BeadRow]) -> str:
    """Return a 3-line wave summary card string."""
    total_tokens = sum(b.total_tokens for b in beads)
    mean_wc = mean(b.wall_clock_s for b in beads) if beads else 0
    by_status: Counter[str] = Counter(b.status for b in beads)
    blocked = by_status.get("blocked", 0)
    pct_blocked = blocked / len(beads) if beads else 0

    status_line = "  ".join(
        f"{v} {k}" for k, v in sorted(by_status.items(), key=lambda x: -x[1])
    )
    blocked_str = f"[yellow]{blocked} blocked[/yellow]" if pct_blocked > 0.33 else f"{blocked} blocked"

    return (
        f"Wave  {wave_id}  |  {len(beads)} beads  |  "
        f"total: {total_tokens/1_000_000:.1f}M tokens  |  mean: {mean_wc/60:.0f}m {mean_wc%60:02.0f}s\n"
        f"Status: {status_line.replace(str(blocked) + ' blocked', blocked_str)}\n"
        + "─" * 66
    )
```
