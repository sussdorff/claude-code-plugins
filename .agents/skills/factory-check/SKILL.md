---
description: Evaluate factory-ready spec quality for a bead before autonomous execution
argument-hint: [bead-id]
tags: workflow
---

# /factory-check — Bead Spec Quality Evaluation

Evaluates a bead's specification against the 6 factory-ready criteria and recommends whether it can be run autonomously or needs interactive work first.

**Usage**: `/factory-check <bead-id>`

## What This Checks

Factory-ready is a **Phase 1 gate** (spec quality, before implementation). It answers: *"Is this spec complete enough for an agent to execute without getting stuck?"*

This is NOT the DoD (Definition of Done). Tests passing, code quality — those are Phase 4. Factory-ready is Phase 1.

## Procedure

### Step 1: Load Bead Data

```bash
bd show $ARGUMENTS --json
```

Extract and note:
- `id`, `title`, `type` (feature/epic/task/bug/chore)
- `description` (full text)
- `acceptance_criteria` (list)
- `metadata.intent`, `metadata.contracts`, `metadata.constraints`
- `blocked_by` (list of blocker IDs)
- `metadata.effort` (if present)

### Step 2: Evaluate Each Criterion

Evaluate all 6 criteria against the bead data. For each criterion, assign PASS / WARN / FAIL.

#### Criterion 1: Clear Intent (Description Quality)

- PASS: Description is non-empty AND has >20 words AND clearly states what changes
- WARN: Description exists but is thin (<20 words or lacks context)
- FAIL: Empty, "TBD", placeholder, or so vague multiple interpretations exist

#### Criterion 2: Outcome-Focused Acceptance Criteria

- PASS: At least 1 AC exists AND ACs describe observable outcomes (not implementation steps)
- WARN: ACs exist but are phrased as implementation tasks ("Implement X", "Write code for Y")
- FAIL: No ACs present

#### Criterion 3: Means of Compliance (MoC) Table

- PASS: Description contains a MoC table (markdown pipe table with MoC/verification column)
- WARN (task/bug only): No MoC table, but bead type makes it optional
- FAIL (feature/epic): No MoC table — agent cannot know how to verify each AC

Check for MoC table: look for a markdown table in the description containing keywords like "MoC", "unit", "e2e", "integ", "review", "demo", "doc".

#### Criterion 4: NLSpec / Design Populated

- SKIP: Bead type is task, bug, or chore (not required)
- PASS: `metadata.intent` is non-empty AND describes behavioral goal + scope
- WARN: `metadata.intent` exists but is thin; `metadata.contracts` empty for non-trivial feature
- FAIL: `metadata.intent` is null/empty for a feature or epic

#### Criterion 5: Sizing Validated

- PASS: Single concern, no signs of mixed scope, effort is reasonable (≤5)
- WARN: Effort is high (>5) OR description hints at multiple concerns
- FAIL: Epic-level scope packed into single bead, multiple unrelated features described

#### Criterion 6: Dependencies Resolved

- PASS: `blocked_by` is empty or null
- FAIL: `blocked_by` contains open bead IDs

For any non-empty `blocked_by`, verify blocker status:
```bash
bd show <blocker-id> --json | jq -r '.[0].status'
```
If all blockers are "closed", mark as PASS.

### Step 3: Compute Score and Verdict

Apply scoring based on bead type (see `standards/workflow/factory-ready.md` for the full required/optional table):

Required criteria by type:
- **feature/epic**: All 6 criteria required (Criterion 4 required)
- **task/bug**: Criteria 1, 2, 5, 6 required; Criterion 3 recommended; Criterion 4 skip
- **chore**: Only Criterion 6 required; rest optional

Verdict logic:
- Any required criterion is FAIL → **NEEDS INTERACTIVE WORK**
- All required criteria PASS, some WARNs → **FACTORY READY with warnings**
- All required criteria PASS, no WARNs → **FACTORY READY**

### Step 4: Output Report

Format the report as:

```markdown
## Factory-Ready Check: <bead-id> — <title>

**Type**: <type> | **Effort**: <effort or "not set">

### Criteria Evaluation

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| 1 | Clear intent in description | PASS/WARN/FAIL | [specific finding] |
| 2 | Outcome-focused ACs | PASS/WARN/FAIL | [X ACs found / issue] |
| 3 | MoC table present | PASS/WARN/FAIL/SKIP | [found/missing] |
| 4 | NLSpec intent/contracts | PASS/WARN/FAIL/SKIP | [populated / missing / not required] |
| 5 | Sizing validated | PASS/WARN/FAIL | [single concern / mixed scope] |
| 6 | Dependencies resolved | PASS/FAIL | [no blockers / blocked by X] |

### Verdict

**FACTORY READY** ✓ — Can run autonomously: `cld -b <id>` or `/impl <id>`

— OR —

**NEEDS INTERACTIVE WORK** — Spec gaps prevent autonomous execution:
- [Gap 1: specific missing element]
- [Gap 2: specific missing element]

**Recommended action**: Run `/plan <id>` to resolve the above gaps before autonomous execution.

### Warnings (non-blocking)
- [Any WARN items that won't block execution but may cause issues]
```

## Decision Reference

| Verdict | What to Do |
|---------|-----------|
| FACTORY READY | `cld -b <id>` for background run, or `/impl <id>` in current session |
| FACTORY READY with warnings | Proceed with caution; note warnings in session |
| NEEDS INTERACTIVE WORK | Run `/plan <id>` first to fill spec gaps |
| BLOCKED | Resolve blockers before anything else |

## Reference

Full criteria details, scoring table, and quick-check procedure: `malte/standards/workflow/factory-ready.md`
