---
name: nbj-audit
model: sonnet
description: >-
  Audit a codebase against Nate's 12 NBJ agent primitives and produce a scored
  scorecard with risk levels and delta tracking. Triggers on: nbj audit, agent
  primitives audit, harness audit, 12 primitives check, plumbing audit.
requires_standards: [english-only]
---

# NBJ Audit

Score a codebase against the 12 NBJ agent-architecture primitives ("Building Agents Is 80% Plumbing"). Produces a scorecard with status (present/partial/missing), risk levels, delta from previous run, and top priorities.

## When to Use

- "run nbj audit" / "audit agent primitives" / "harness audit"
- "score against 12 primitives" / "plumbing audit"
- "how complete is our agent harness?"

## Workflow

### 1. Load Primitives Framework

Read `references/primitives.md` now — scoring criteria and tier thresholds.

### 2. Detect Mode and Run Inventory

```bash
scripts/nbj-audit.sh [project-root]
```

Default project-root = cwd. Script auto-detects mode:
- **harness**: cwd contains a harness skills directory AND a harness agents directory (see harness adapter for exact paths)
- **project**: everything else

### 3. Parse Inventory

Extract from script output:
- `mode=` and `project=` for header
- `PRIMITIVE: N | name | status=X | finding` — one line per primitive
- `HISTORY:` line — exists or missing
- `HISTORY_LAST_RUN:` — timestamp of previous run if exists

### 4. Load Delta (if history exists)

If `HISTORY: ... exists`, read `.beads/nbj-audit-history.json` to get previous primitive statuses. Compute delta per primitive:
- `↑` improved, `↓` regressed, `=` unchanged, `new` not in prior run

If no history: all deltas show `-`.

### 5. Evaluate and Score

For each primitive, use the inventory finding + `references/primitives.md` criteria to confirm the script's status. Override if the evidence clearly contradicts.

WHY: The script does mechanical detection; you add judgment for edge cases.

Load `references/evaluation-guide.md` only if status is ambiguous or you need to investigate further.

### 6. Output Scorecard

```
## NBJ Harness Audit — {project} ({mode} mode)
Run: {timestamp}

| # | Primitive | Status | Finding | Risk | Delta |
|---|-----------|--------|---------|------|-------|
| 1 | Tool Registry | present | 52 skills in <skills-dir>/ | low | = |
...

### Assessment Overview
**Tier:** Tier 2: Operational (6/12 present)
**Highest Risk:** [primitive name] — [one sentence why]

### Top 3 Priorities
1. [highest impact missing/partial primitive]
2. ...
3. ...

### Verification Checks
- [ ] [Concrete invariant test 1]
- [ ] [Concrete invariant test 2]
- [ ] [Concrete invariant test 3]
```

Risk mapping: `present` → low, `partial` → medium, `missing` → high.

Tier thresholds (count of `present` primitives):
- 0–4: Tier 1: Foundational
- 5–8: Tier 2: Operational
- 9–12: Tier 3: Advanced

### 7. Save History

After outputting the scorecard, save results to `.beads/nbj-audit-history.json`:

```json
{
  "runs": [
    {
      "timestamp": "<iso8601>",
      "mode": "<mode>",
      "primitives": { "1": "present", "2": "partial", ... }
    }
  ]
}
```

Append the new run to existing `runs` array (or create file if missing). Cap history at 10 runs.

WHY: Enables delta tracking on the next run.

## Do NOT

- Report primitives without running the inventory script first
- Skip delta calculation when history exists
- Modify source files — audit only
- Save history if the user explicitly asks for a dry run

## Resources

- `references/primitives.md` — 12 primitives + scoring criteria (load always)
- `references/evaluation-guide.md` — Where to look per primitive, per mode (load on demand)
- `scripts/nbj-audit.sh` — Inventory collector
