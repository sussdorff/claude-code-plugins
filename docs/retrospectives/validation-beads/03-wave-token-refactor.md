---
title: "Refactor wave orchestrator token-budget helpers into shared module"
description: >
  The wave orchestrator (beads-workflow/agents/wave-orchestrator.md) contains
  inline token-budget arithmetic duplicated across three places: wave sizing,
  per-bead budget allocation, and rollup reporting. Extract these into a
  shared Python helper `beads-workflow/lib/orchestrator/token_budget.py` with
  typed functions and unit tests.
type: task
effort: medium
rubric_weight: 2
expected_complexity: mechanical extraction — move code, update imports, add tests
---

## Scenario

A developer adding a new wave mode notices that the token-budget calculation
`reserved = total_budget * 0.1` appears verbatim in three places across the
orchestrator docs and the metrics module. Any adjustment to the reservation
percentage requires three edits. The refactor extracts this into a single
module with documented constants and pure functions.

## Acceptance Criteria

- New file `beads-workflow/lib/orchestrator/token_budget.py` with at minimum:
  - `RESERVATION_FACTOR: float = 0.1`
  - `compute_per_bead_budget(total: int, bead_count: int) -> int`
  - `compute_reserved(total: int) -> int`
- All three original call sites updated to import from `token_budget`
- `tests/orchestrator/test_token_budget.py` with ≥4 parametrized cases
- No behavioural change — existing metric values unchanged
- Type annotations throughout

## MoC Table

| Metric | Before | After |
|--------|--------|-------|
| Duplication instances of budget arithmetic | 3 | 1 |
| Unit tests for budget logic | 0 | ≥4 |

## Baseline Sketch

```python
# beads-workflow/lib/orchestrator/token_budget.py (new)
"""Shared token-budget helpers for wave orchestration."""

RESERVATION_FACTOR: float = 0.10
"""Fraction of total budget held back for overhead (review, MoC, changelog)."""


def compute_reserved(total: int) -> int:
    """Return tokens reserved for orchestration overhead."""
    return int(total * RESERVATION_FACTOR)


def compute_per_bead_budget(total: int, bead_count: int) -> int:
    """Return per-bead token budget after deducting reservation."""
    if bead_count <= 0:
        raise ValueError("bead_count must be positive")
    usable = total - compute_reserved(total)
    return usable // bead_count
```

```python
# beads-workflow/lib/orchestrator/routing.py — before
reserved = total_budget * 0.1
per_bead = (total_budget - reserved) // bead_count

# after
from .token_budget import compute_per_bead_budget
per_bead = compute_per_bead_budget(total_budget, bead_count)
```
