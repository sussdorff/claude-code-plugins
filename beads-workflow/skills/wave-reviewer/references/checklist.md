# Wave Reviewer Checklist

Use this checklist to review a wave candidate or epic subtree as a system.

## 1. Dependency Graph

Ask:
- Does every blocker actually need to come first?
- Is any bead missing a blocker that its contract clearly depends on?
- Is cleanup/deletion blocked on validation, not just implementation?
- Are waves sequenced so migration lands before enforcement or removal?

Look for:
- deletion before comparison
- enforcement before helper/migration
- validation blocked on reporting polish instead of true prerequisites

## 2. Ownership

Ask:
- Who is the single owner of each interface, schema, helper, insert API, and lifecycle contract?
- Are two beads both "sort of" owning the same thing?
- Does a consumer depend on an API that no producer explicitly promises?

Look for:
- schema split between migration bead and wrapper bead
- helper ownership implied but not accepted
- rollup logic owned nowhere

## 3. Lifecycle Side Effects

Ask:
- What does this bead merge, push, close, tag, delete, or persist?
- Does that side effect invalidate a later bead's assumptions?
- Can the validation path run without mutating the baseline it is supposed to compare?

Look for:
- session-close mutating main during A/B validation
- cleanup destroying evidence needed later
- closing a bead that must remain open on veto

## 4. Identity Model

Ask:
- What uniquely identifies a run, comparison unit, artifact, or measurement row?
- Can retries, replays, and paired validations be distinguished?

Look for:
- `bead_id` used where `run_id` is required
- child rows linked to non-unique parents
- validation comparing siblings without per-run attribution

## 5. Validation Methodology

Ask:
- Does the proposed experiment isolate the variable it claims to measure?
- Does one arm contaminate the other?
- Are exclusion criteria defined up front?

Look for:
- different beads used as A/B arms
- mutable baseline between trials
- quality judged without a rubric

## 6. Acceptance Branch Coverage

Ask:
- Could the bead pass while the risky branch never executed?
- Are conditional failure paths explicitly exercised?

Look for:
- only happy-path tests
- no forced-path fixtures for conditional phases
- acceptance that proves docs changed but not behavior

## 7. Agent / Tool Contract Feasibility

Ask:
- Does the bead ask an agent or tool to do something it cannot do?
- Is note persistence, file writing, or bead mutation assigned to the right actor?

Look for:
- read-only agent expected to `bd update`
- skill expected to infer process facts from diff artifacts
- wrapper expected to self-heal schema it does not own

## 8. Trinity Coherence

Apply only when the bead set touches architectural contracts.

Ask:
- Is the ADR named?
- Is the Helper identified?
- Are proactive and reactive enforcers distinguished correctly?
- Is the wave sequencing sane across ADR / Helper / Enforcer work?

Look for:
- missing ADR owner
- reactive enforcer without helper path
- allowlist debt hidden inside "done"
- pre-trinity package left uncovered while enforcement is added elsewhere

## 9. Migration Shape

Ask:
- Is this migration / validation / cleanup / steady-state work clearly labeled?
- Are non-goals explicit?
- Is there a rollback or fallback if the preferred design is infeasible?

Look for:
- migration bead pretending to be cleanup
- validation bead with no fallback harness
- design-only bead that accidentally implies implementation

## 10. Minimal Fix Discipline

After finding a defect, propose the smallest change that restores coherence:
- split a bead
- add one dependency
- narrow scope
- strengthen acceptance
- move ownership explicitly

Prefer minimal graph edits over rewriting the whole tree.

## Per-Bead Quality Checks

Evaluate each bead in the review set against this A/B/C rubric. Score is recorded in the Phase 1 bead table and feeds automatic MEDIUM findings.

### A — Fully factory-ready spec

All of the following must hold:
- Description > 20 words and clearly states what changes
- At least 1 outcome-focused AC (not implementation steps)
- For features/epics: MoC table present in description
- For features/epics: `metadata.intent` populated (non-empty)
- Single-concern scope (no mixed scope)

### B — Usable but has warnings

Meets A criteria partially — at least one of:
- Thin description (< 20 words or lacks context)
- ACs present but phrased as implementation tasks ("Implement X", "Write code for Y")
- Missing MoC table (feature/epic only)
- Missing `metadata.intent` (feature/epic only)

Not fatally broken — an agent can proceed with caution.

### C — Needs interactive work

Any of the following disqualifies the bead:
- Empty, "TBD", or placeholder description
- No ACs present at all
- Feature or epic without a MoC table
- Feature or epic without `metadata.intent`
- Mixed scope / epic-level work packed into a single bead

### Automatic MEDIUM Finding Rule

Generate a MEDIUM finding in the wave Findings table whenever:
- Any bead scores **C** (always, regardless of type)
- A **feature or epic** bead scores **B** (partial spec is insufficient for autonomous execution of high-scope work)

Do NOT generate a finding for task/bug/chore beads that score B.

Finding format:

```
- MEDIUM — <bead-id> — Bead quality score <B/C> (bead_quality): <specific gap>. Fix: <minimal action to reach A>.
```

Example:

```
- MEDIUM — CCP-xyz — Bead quality score C (bead_quality): no acceptance criteria present. Fix: add at least 1 outcome-focused AC before dispatch.
```
