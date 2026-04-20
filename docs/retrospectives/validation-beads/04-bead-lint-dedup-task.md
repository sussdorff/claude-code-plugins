---
title: "Deduplicate bead-lint rule registry — merge overlapping title checks"
description: >
  The bead-lint validator (scripts/validate-bead.py or equivalent) has three
  separate regex checks for bead title formatting that partially overlap and
  produce redundant warnings. Consolidate them into a single structured rule
  with a shared message and a combined regex, reducing false-positive noise
  in CI output.
type: task
effort: medium
rubric_weight: 2
expected_complexity: mechanical dedup — consolidate regexes, update test fixtures
---

## Scenario

A developer runs `bd lint <id>` and sees three nearly identical warnings:

```
WARN  title: missing [VAL] prefix
WARN  title: [VAL] prefix not at start
WARN  title: prefix format mismatch
```

All three fire on the same title. Investigation reveals three separate `RuleCheck`
objects in the registry whose patterns overlap. Consolidating them removes the
noise and makes CI output actionable (one finding, one fix).

## Acceptance Criteria

- The three overlapping title-prefix checks are merged into one `RuleCheck`
  named `title-prefix-format` with a single combined regex
- Running `bd lint` on a non-conformant title produces exactly one WARN (not three)
- Running `bd lint` on a conformant title produces zero WARNs related to prefix
- Existing test fixtures updated to reflect new single-warning behaviour
- No other lint rules changed

## MoC Table

| Metric | Before | After |
|--------|--------|-------|
| Warnings per non-conformant title | 3 | 1 |
| Rule registry entries for title-prefix | 3 | 1 |

## Baseline Sketch

```python
# scripts/validate-bead.py — before
RULES = [
    RuleCheck("title-missing-val",    r"^\[VAL\]",           "missing [VAL] prefix"),
    RuleCheck("title-val-not-start",  r"^\[VAL\] \S",        "[VAL] prefix not at start"),
    RuleCheck("title-prefix-mismatch",r"^\[VAL\] [A-Z]",     "prefix format mismatch"),
]

# after
RULES = [
    RuleCheck(
        "title-prefix-format",
        r"^\[VAL\] [A-Za-z]",
        "title must start with '[VAL] ' followed by a letter",
    ),
]
```
