# Retro Skill Reference

## Methods Catalog

The retro-methods catalog (`standards/retro-methods.yml`) contains 4 methods:

### 4Ls (default)
**Signal:** none / balanced data
**Rounds:** Liked → Learned → Lacked → Longed-for

General-purpose method when no specific problem pattern dominates. Good for regular
bi-weekly cadence when things are running smoothly.

### 5 Whys
**Signal:** `recurring_problems`, `high_churn`
**Rounds:** Surface → Why 1-2 → Why 3-4 → Root + Fix

Root cause analysis for when the same issue keeps appearing. Each round drills deeper
into causality. Also triggered by high churn (excessive review cycles or force-pushes),
which often indicates a recurring structural problem.

### Energy Radar
**Signal:** `low_energy`
**Rounds:** Energy Map → Drain Analysis → Source Amplification → Rebalance Plan

Maps energy across work categories. Triggered when open-brain timeline shows low
confidence scores or predominantly negative sentiment. Focuses on identifying what
drains vs. energizes, then rebalancing.

### Data Deep-Dive
**Signal:** `data_heavy`
**Rounds:** Cost Landscape → Ratio Analysis → Trend Detection → Efficiency Targets

Quantitative analysis of bead metrics. Triggered when token costs show outliers
(beads costing >2x the median). Turns numbers into actionable efficiency targets.

## Adding New Methods

Add entries to `standards/retro-methods.yml` following this structure:

```yaml
- name: "Method Name"
  signal_match:
    - "signal_type"    # Must match a signal from Phase 3 detection
  description: >-
    When to use this method and what it achieves.
  round_prompts:
    - "Round 1 prompt — specific perspective and guiding questions"
    - "Round 2 prompt — different angle on the same data"
    - "Round 3 prompt — synthesis or deeper analysis"
    - "Round 4 prompt — action-oriented conclusion"
```

Each method must have exactly 4 `round_prompts`. The signal_match list can include
multiple signals (the method will be suggested when any matched signal is detected).

## Action Bead Lifecycle

```
/retro creates action beads
    │
    ▼
bd create --type=task --priority=2 --labels=retro-action --title="[RETRO-ACTION] ..."
    │
    ▼
Next /retro run checks: bd list --label=retro-action
    │
    ├── done → reported as complete
    ├── in_progress → reported, continues
    └── open → user decides: carry over or archive
```

The `retro-action` label is the linkage between retro runs. Without it, action
follow-up breaks silently.
