---
name: wave-reviewer
description: >-
  Review a wave or epic subtree before dispatch. Finds defects single-bead
  review misses: dependency ordering, ownership collisions, lifecycle
  contradictions, validation gaps. Triggers on wave review, review wave,
  pre-wave review, bead tree review.
---

# /wave-reviewer

## Overview

Cross-bead structural review for a wave or epic subtree.

Use this after filing multiple beads and before dispatching a wave, validation run,
cleanup wave, or deletion wave.

Contrast with single-bead review:
- Single-bead review asks "is this bead locally reasonable?"
- `/wave-reviewer` asks "does this bead set work as one machine?"

## When to Use

- Review a full epic subtree before dispatch
- Review only the next ready wave from an epic
- Review an explicit set of beads as one candidate wave
- Review a validation or cleanup wave before it mutates the baseline

Accepted inputs:

```text
/wave-reviewer <epic-id>
/wave-reviewer <bead-id-1> <bead-id-2> <bead-id-3>
/wave-reviewer --ready <epic-id>
```

Interpretation modes:

| Invocation | Mode | Behavior |
|---|---|---|
| One epic ID | Epic subtree review | Review the parent plus all currently linked child beads |
| Multiple bead IDs | Explicit wave review | Review exactly the named beads as a candidate wave |
| `--ready <epic-id>` | Ready-only wave review | Review only the ready children of the epic as a wave candidate |

If the input is ambiguous, ask the user whether to review:
- the full epic subtree, or
- only the next dispatch wave

## Core Principle

Do not trust bead prose alone.

Every finding should be grounded in at least one of:
- bead text
- dependency graph shape
- real code / agent / skill / script contract in the repo
- real lifecycle behavior already documented in the repo

If a bead references a file, table, agent, mode, wrapper, schema, or hook, verify it in
the codebase before calling it a defect.

## Workflow

### Phase 1: Load the bead set

1. Resolve the review set:
   - Epic mode: load the parent bead and all children
   - Explicit mode: load all named beads
   - `--ready`: load the epic, then keep only ready children
2. For each bead, collect:
   - title
   - type / priority / status
   - dependencies and blockers
   - acceptance criteria
   - notes
3. Build a simple review table:

```markdown
| Bead | Type | Ready | Depends On | Blocks |
|---|---|---|---|---|
```

### Phase 2: Extract the real contracts

For the loaded bead set, extract all references to real implementation contracts:
- file paths
- scripts
- agents
- skills
- tables / schemas
- environment vars
- flags / modes
- lifecycle verbs like merge, push, close, tag, session-close

Then verify them with repo reads/searches.

Examples:
- If a bead says an agent writes to notes, verify the agent has tools to do that.
- If a bead says validation compares two runs, verify the metrics identity model can distinguish them.
- If a bead says cleanup happens after validation, verify dependency order actually enforces that.

### Phase 3: Run the structural checklist

Use the checklist in `references/checklist.md`.

Do not stop at the first defect. Review the whole wave.

### Phase 4: Trinity pass

When beads touch architectural contracts, use the Architecture Trinity vocabulary precisely:
- ADR
- Helper
- Enforcer-Proactive
- Enforcer-Reactive

Check whether the bead set is coherent at the contract layer:
- Is there a bead creating or changing the ADR without the corresponding Helper or Enforcer follow-up?
- Is a reactive enforcer being added before the migration/helper work that makes compliance practical?
- Is a bead claiming to enforce a contract without naming the contract owner?
- Is a migration wave missing a coverage or allowlist-burndown follow-up?

Do not force Trinity language onto beads that are not contract-related.

### Phase 5: Decide whether the wave is structurally ready

Possible outcomes:
- `Structurally ready`
- `Ready after minor edits`
- `Not ready for dispatch`

This is not a code-quality verdict. It is a wave-structure verdict.

## Output

Findings first, ordered by severity.

Output format:

```markdown
## Findings

- HIGH — <bead-id[, bead-id]> — <specific contradiction or structural risk>. Fix: <minimal change>.
- MEDIUM — <bead-id[, bead-id]> — <specific contradiction or structural risk>. Fix: <minimal change>.

## Ready Verdict

<Structurally ready | Ready after minor edits | Not ready for dispatch>

## Open Questions

- <only if truly unresolved>
```

Rules:
- Keep findings concrete
- Name the affected bead IDs
- Cite the exact contract you checked when possible
- Prefer the smallest fix that removes the contradiction
- Do not pad the output with summaries before findings

## Finding Calibration

Good:
- "Cleanup bead deletes the old control arm before validation bead can run the comparison."
- "Wrapper bead depends on helper API that no other bead explicitly owns."
- "Validation bead compares same logical bead twice, but session-close mutates main between runs."

Weak:
- "This feels risky."
- "Maybe add more tests."
- "The wording could be clearer."

## Example

```text
/wave-reviewer CCP-2vo
```

Possible result:

```markdown
## Findings

- HIGH — CCP-2vo.6, CCP-2vo.8 — Cleanup deletes the legacy review path before the validation wave can use it as the control arm. Fix: split migration from deletion and block deletion on validation verdict.
- MEDIUM — CCP-2vo.3, CCP-2vo.2 — Wrapper bead depends on a shared metrics helper, but the schema bead does not yet own that API contract. Fix: move helper ownership explicitly into the schema bead acceptance.

## Ready Verdict

Ready after minor edits
```

## Follow-Up Beads

If the same class of defects appears across multiple newly created beads, suggest a follow-up
against the bead-generation workflow rather than patching each bead forever.

Typical triggers:
- missing ownership statements
- missing lifecycle side effects
- missing negative-path acceptance cases
- sloppy dependency rationale
- contract-related beads using Trinity terms inconsistently

That follow-up belongs in bead generation, not in `/wave-reviewer`.

## Resources

- `references/checklist.md` — Full structural checklist for wave-level review

## Limitations

- Do review the whole wave as a system
- Do cross-check bead claims against real repo contracts
- Do use Trinity vocabulary when contracts are involved
- Do not implement code
- Do not auto-edit beads unless the user explicitly asks
- Do not create follow-up beads automatically
- Do not collapse findings into a bland score
