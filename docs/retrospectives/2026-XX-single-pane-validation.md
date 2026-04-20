# Retrospective: Single-Pane Orchestration A/B Validation

**Epic:** CCP-2vo  
**Status:** TBD — runs not yet complete  
**Date:** 2026-XX (fill in when all runs complete)

---

## Methodology

### Background

CCP-2vo.1 through CCP-2vo.7 implemented a single-pane (`full-1pane`) orchestration
mode that consolidates the two-terminal (main pane + review pane) workflow into one.
The hypothesis is that single-pane reduces total token cost while maintaining
implementation quality.

### Validation Approach

We use **paired sibling beads** with **blind scoring**:

1. Six canonical validation beads were defined (see `docs/retrospectives/validation-beads/`).
   Each represents a realistic unit of work across three complexity tiers:
   micro bug, medium task, medium feature.

2. For each canonical bead, two sibling beads were created with opaque slugs
   (no `run-A` / `run-B` naming that could bias the scorer).

3. Each sibling is dispatched with `--validation-mode=true`, which captures
   metrics but skips the lifecycle-mutating session-close (no merge/push/tag).
   Both siblings in a pair start from the same `git rev-parse HEAD` SHA.

4. After all 12 runs, an Opus subagent scores each diff against the quality rubric
   without seeing arm labels. Scores are then joined back to arms using
   `arm-mapping.md` (kept separate to prevent leakage into the scorer context).

5. Pairwise deltas determine the verdict.

### Rubric

Scores are 0–10 per dimension, then weighted by `rubric_weight` (1=micro, 2=medium-task, 3=medium-feature).

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Acceptance criteria met | 30% | All AKs from canonical bead satisfied |
| Code correctness | 25% | No obvious bugs, handles edge cases |
| Test coverage | 20% | Tests written, realistic, passing |
| Code quality | 15% | Clean, idiomatic, well-named |
| Diff hygiene | 10% | No unrelated changes, minimal noise |

**Overall quality_score = weighted sum of dimension scores (0–10)**

Threshold: quality_score ≥ 6.5 is considered acceptable. A delta of -0.5 or
better between treatment and control is acceptable (treatment may be marginally
lower quality if token savings are significant).

---

## Per-Run Data

Fill this table after each run completes.

| canonical | slug | bead_id | arm | main_sha | run_id | total_tokens | wall_clock_s | quality_score | verdict |
|-----------|------|---------|-----|----------|--------|-------------|-------------|---------------|---------|
| 01-metrics-rollup-null-bug  | xjmt | CCP-2vo.8.1  | full-2pane | — | — | — | — | — | — |
| 01-metrics-rollup-null-bug  | kpnv | CCP-2vo.8.2  | full-1pane | — | — | — | — | — | — |
| 02-codex-exec-timeout-bug   | bqwr | CCP-2vo.8.3  | full-2pane | — | — | — | — | — | — |
| 02-codex-exec-timeout-bug   | fhzd | CCP-2vo.8.4  | full-1pane | — | — | — | — | — | — |
| 03-wave-token-refactor      | cysn | CCP-2vo.8.5  | full-2pane | — | — | — | — | — | — |
| 03-wave-token-refactor      | gltu | CCP-2vo.8.6  | full-1pane | — | — | — | — | — | — |
| 04-bead-lint-dedup-task     | dpek | CCP-2vo.8.7  | full-2pane | — | — | — | — | — | — |
| 04-bead-lint-dedup-task     | hwqf | CCP-2vo.8.8  | full-1pane | — | — | — | — | — | — |
| 05-metrics-endpoint-feature | ergx | CCP-2vo.8.9  | full-2pane | — | — | — | — | — | — |
| 05-metrics-endpoint-feature | ivcm | CCP-2vo.8.10 | full-1pane | — | — | — | — | — | — |
| 06-wave-report-ui-feature   | fzlb | CCP-2vo.8.11 | full-2pane | — | — | — | — | — | — |
| 06-wave-report-ui-feature   | jpas | CCP-2vo.8.12 | full-1pane | — | — | — | — | — | — |

---

## Pairwise Delta Summary

Fill this section after scoring is complete.

| canonical | delta_tokens (control−treatment) | delta_quality (treatment−control) | token_savings_pct | verdict |
|-----------|----------------------------------|-----------------------------------|-------------------|---------|
| 01-metrics-rollup-null-bug  | — | — | — | — |
| 02-codex-exec-timeout-bug   | — | — | — | — |
| 03-wave-token-refactor      | — | — | — | — |
| 04-bead-lint-dedup-task     | — | — | — | — |
| 05-metrics-endpoint-feature | — | — | — | — |
| 06-wave-report-ui-feature   | — | — | — | — |
| **Weighted mean**           | — | — | — | — |

---

## Verdict

**KEEP / TUNE / REVERT — TBD after runs complete**

Decision criteria:
- **KEEP**: weighted mean token savings ≥ 10% AND weighted mean quality delta ≥ -0.5
- **TUNE**: token savings are real but quality delta < -0.5 for ≥2 canonicals → investigate which phases drive quality loss, tune and re-test
- **REVERT**: no consistent token savings OR quality degradation > 1.0 on any canonical

---

## Exclusion Criteria

A run pair is excluded from analysis if any of the following apply:

1. **SHA divergence**: main SHA changed between the two siblings of a pair (external merge happened during dispatch window)
2. **Early crash**: either run exited before Phase 5 (implementation) with an unhandled error
3. **Empty diff**: the diff is empty or contains only whitespace changes (indicates a dispatch or bead-setup error)
4. **Both arms poor**: `quality_score ≤ 3.0` for both arms in a pair (canonical bead may be malformed or unimplementable as written)

Excluded pairs are noted here with reason:

| canonical | excluded? | reason |
|-----------|-----------|--------|
| 01-metrics-rollup-null-bug  | — | — |
| 02-codex-exec-timeout-bug   | — | — |
| 03-wave-token-refactor      | — | — |
| 04-bead-lint-dedup-task     | — | — |
| 05-metrics-endpoint-feature | — | — |
| 06-wave-report-ui-feature   | — | — |

If > 2 pairs are excluded: re-run with replacement canonicals before writing final verdict.

---

## Qualitative Notes

*(Fill in after reviewing diffs and scorer notes)*

### Patterns observed in full-2pane runs

- 

### Patterns observed in full-1pane runs

- 

### Unexpected findings

- 

### Recommendations for follow-up

- 
