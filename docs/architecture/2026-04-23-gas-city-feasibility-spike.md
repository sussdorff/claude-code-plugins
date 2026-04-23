# Gas City Feasibility Spike

**Bead:** CCP-elb
**Date:** 2026-04-23
**Status:** Planned

---

## Purpose

Decide whether we should start a narrow Gas City pilot now, or keep observing,
without extending the custom `wave-orchestrator` in the meantime.

This spike is explicitly a feasibility check for orchestration infrastructure.
It is **not** a migration and **not** a scheduler rewrite.

---

## Current Decision Context

- The custom `wave-orchestrator` is in feature freeze.
- Only correctness / safety bug fixes are allowed until this spike is done.
- The strategic question is no longer "should we add rolling waves?" but
  "can Gas City absorb enough orchestration responsibility that further custom
  scheduler work is irrational?"

### External baseline checked on 2026-04-23

- Gas City GitHub releases currently show `v0.15.1` on 2026-04-17, not `v1.0.0`.
- Gas City docs were updated recently:
  - PackV2 guide: 2026-04-16
  - Quickstart: 2026-04-19
  - Coming from Gas Town: 2026-04-19
- Gas City docs clearly support formulas, `needs`, orders, and durable waits.
- Gas City docs also state that formula resolution exists, but real multi-step
  execution remains backend-dependent today, with `bd` as the production path.

Sources:
- https://github.com/gastownhall/gascity/releases
- https://github.com/gastownhall/gascity
- https://docs.gascityhall.com/getting-started/coming-from-gastown
- https://docs.gascityhall.com/guides/migrating-to-pack-vnext
- https://docs.gascityhall.com/tutorials/05-formulas
- https://docs.gascityhall.com/reference/cli

---

## Questions To Answer

| Question | Why it matters | Required output |
|---|---|---|
| Mutex semantics | Our `adapter-common` conflict is not a dependency edge | `native` / `via pack` / `external layer` / `unsupported` |
| Wait / barrier semantics | We need a clean replacement for human or phase barriers | `native` / `via pack` / `external layer` / `unsupported` |
| Gate-mutation boundary | Our current system can split beads, add deps, supersede, and create remediation beads | `native` / `via pack` / `external layer` / `unsupported` |
| PackV2 adoption risk | The pilot should avoid port-churn and accidental Big Bang migration | `low` / `medium` / `high` with rationale |

---

## Spike Scope

Timebox: 1 day.

Build only enough to answer the questions above:

1. Create a disposable Gas City sandbox.
2. Model a tiny 3-item work graph.
3. Add one barrier / wait case.
4. Attempt one mutex-style conflict case.
5. Classify what belongs in Gas City primitives versus an external gate layer.

Out of scope:

- Production migration
- Porting existing agents or skills
- Replacing the custom `wave-orchestrator`
- Solving every long-tail architecture concern now

---

## Proposed Mini Test Matrix

### Test A: Basic DAG

Goal: verify that a tiny topological flow works as expected.

- `A` has no deps
- `B` needs `A`
- `C` needs `A`

Expected: `A` first, `B` and `C` fan out after `A`.

### Test B: Durable Barrier

Goal: verify whether waits can represent a clean operator barrier.

- Insert a manual or durable wait between two formula stages.
- Confirm how the wait is inspected, resumed, and observed.

Expected: barrier behavior exists without custom scheduler code.

### Test C: Mutex-Style Conflict

Goal: determine whether Gas City can model "may not run concurrently" without
lying with dependency edges.

- Two items are dependency-independent.
- Both claim the same synthetic shared resource.

Expected:
- Either a real named lock / semaphore mechanism exists,
- or the gap is confirmed and classified as `via pack` or `external layer`.

### Test D: Gate-Mutation Boundary

Goal: decide whether our gates belong inside formulas or around them.

- Simulate a pre-dispatch gate that changes the work graph.
- Simulate a post-run verification step that emits remediation work.

Expected:
- Clear ownership boundary:
  - `inside Gas City`
  - `pack/order layer`
  - `external graph compiler / remediation producer`

---

## Evaluation Rules

The spike is successful if it reduces decision ambiguity, not if it proves that
Gas City can do everything.

Use these rules:

- Prefer a narrow pilot if waits and DAG behavior are solid, even if
  gate-mutation stays outside the formula runtime.
- Treat missing named mutex support as the highest-risk gap.
- Treat PackV2 churn as acceptable for a pilot if only a small surface is
  touched.
- Reject Big Bang thinking: pilot scope must stay mutex-light and small.

---

## Planned Output

At the end of the spike, produce:

1. A verdict table with one row per question.
2. A pilot recommendation:
   - start now
   - start with constraints
   - wait and re-check later
3. A candidate pilot shape:
   - prefer a mutex-free or mutex-light epic
   - keep existing skills / standards / review logic unchanged
   - swap only orchestration infrastructure where proven

---

## Default Recommendation Threshold

Proceed to pilot if all of the following are true:

- DAG + wait semantics are adequate
- PackV2 risk is acceptable for a small pilot
- Gate-mutation can be cleanly kept outside the formula runtime if needed
- Mutex is either supported well enough or can be avoided in the first pilot

Keep monitoring instead of piloting only if one of these is true:

- waits are too weak for practical barrier handling
- mutex cannot be expressed and cannot be cleanly externalized
- PackV2 churn would force immediate broad porting work

