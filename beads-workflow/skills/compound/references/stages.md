# Compound Retrospective — Stage-by-Stage Guide

Detailed guidance for running each of the 4 stages. Load this reference when you need
question banks, decision heuristics, or example artifacts.

## Stage 1: Requirements vs Strategy

**Goal:** Identify gaps between what was asked and what was planned.

### Information to Gather

```bash
bd show <bead-id>          # Acceptance criteria, title, description, labels
cat ~/.claude/plans/<bead-id>.md 2>/dev/null  # Plan file if it exists
```

### Question Bank

- Did every acceptance criterion have a corresponding plan task?
- Were any acceptance criteria ambiguous? How was the ambiguity resolved?
- Was the scope implicitly expanded or contracted during planning?
- Were there dependencies or constraints not mentioned in the ticket but discovered during planning?
- Was the effort estimate aligned with the actual ticket complexity?

### Artifact Decision Tree

| Observation | Artifact Type | Action |
|-------------|--------------|--------|
| AC was misread or misinterpreted | Trap | Append to bead notes |
| Scope was explicitly narrowed | Decision | Create decision bead |
| Missing AC discovered late | Trap | Append to bead notes |
| Planning method that worked well | Pattern | Save to open-brain |

### Example Artifacts

**Trap:**
```
TRAP [Stage 1]: Acceptance criteria said "handle errors gracefully" but plan only addressed
happy path. Error handling was left to bugfix phase. Always map each AC to at least one
plan task explicitly.
```

**Decision:**
```
[DECISION] Scope: Skip CSV export for initial release
Context: AC mentioned CSV export but it required new dependency. Deferred to follow-up bead.
Consequences: Users cannot export until next release. No CSV-related tests in scope.
```

---

## Stage 2: Strategy vs Execution

**Goal:** Identify divergence between the plan and what was actually built.

### Information to Gather

```bash
git log --oneline --since="<bead-start-date>"  # Actual commits
git diff <first-commit>..<last-commit> --stat   # Files touched
```

Cross-reference with the plan's task list.

### Question Bank

- Which plan tasks were executed in a different order than planned? Why?
- What was built that was not in the plan?
- What was in the plan but skipped or simplified?
- Were any planned abstractions abandoned in favor of simpler solutions?
- Which implementation choices were made on the fly without conscious decision?

### Artifact Decision Tree

| Observation | Artifact Type | Action |
|-------------|--------------|--------|
| Planned abstraction abandoned | Decision | Create decision bead |
| Unplanned work added scope | Trap | Append to bead notes |
| Simpler approach found during coding | Pattern | Save to open-brain |
| Implementation order mattered unexpectedly | Pattern | Save to open-brain |

### Example Artifacts

**Pattern:**
```
Pattern: When implementing a new data model, write the migration first and run it against
a test DB before writing any application code. This surfaces schema problems before code
is written against the wrong shape.
```

**Trap:**
```
TRAP [Stage 2]: Middleware was added during implementation that wasn't in the plan.
It worked but wasn't tested. Untested middleware caused a regression in Stage 3.
Rule: Any code not in the plan must be explicitly added to the plan (even if tiny).
```

---

## Stage 3: Iteration Review

**Goal:** Learn from the bugfix and refactor cycles that followed the "initial done".

### Information to Gather

```bash
bd show <bead-id>           # Notes, comments with iteration history
git log --oneline --grep="fix\|refactor\|patch"  # Fix/refactor commits
```

Look for commits made after the first "it works" moment.

### Question Bank

- What was the first bug found after implementation?
- Was the bug a logic error, integration issue, or edge case oversight?
- How many "one more fix" commits happened before closing?
- Were any refactors done that should have been in the original implementation?
- Could the bugs have been caught by a different testing approach?
- Was there a pattern to the bugs (all in one layer, all around one data type)?

### Artifact Decision Tree

| Observation | Artifact Type | Action |
|-------------|--------------|--------|
| Same class of bug appeared twice | Trap | Append to bead notes |
| Refactor was predictably needed | Pattern | Save to open-brain |
| Test that would have caught the bug | Pattern | Save to open-brain |
| Architecture forced a workaround | Decision | Create decision bead |

### Example Artifacts

**Trap:**
```
TRAP [Stage 3]: Three separate bugs were all caused by not handling None/null in
user-facing inputs. A single input validation layer at the API boundary would have
prevented all three. Always add explicit None guards at system entry points.
```

**Pattern:**
```
Pattern: After implementing a new feature, write a "destruction test": try to break it
with empty inputs, missing fields, and wrong types. Run this before marking the bead done.
This catches 80% of Stage 3 bugs in Stage 2.
```

---

## Stage 4: Workflow Audit

**Goal:** Identify process friction that slowed delivery or caused errors.

### Information to Gather

No external data needed — this is a reflective stage. Review the session timeline:
- What tools were used? What failed?
- Where was time lost to setup, context-switching, or unclear ownership?
- What information was needed but not immediately available?

### Question Bank

- Which tool invocations had to be retried? Why?
- Was the bead description clear enough to start without asking questions?
- Were there standards or examples that would have saved time?
- Were any decisions made twice (once planned, once re-decided during implementation)?
- Did the skill/agent selection match the actual work?
- What would make the next similar bead faster?

### Artifact Decision Tree

| Observation | Artifact Type | Action |
|-------------|--------------|--------|
| Same question asked multiple times | Trap | Append to bead notes + consider CLAUDE.md update |
| Process step always done but not documented | Pattern | Save to open-brain |
| Tool chosen was wrong for the job | Decision | Create decision bead (tooling choice) |
| Missing standard caused rework | Pattern | Save to open-brain + file REFACTOR bead |

### Example Artifacts

**Pattern (workflow):**
```
Pattern: Before starting any bead involving external APIs, check ~/.claude/standards/
for an existing integration standard. Two beads in a row wasted time re-discovering
the same auth pattern. Standards lookup takes 30 seconds; rediscovery takes 30 minutes.
```

**Trap:**
```
TRAP [Stage 4]: Ran git commit without running tests first because the CI wasn't
configured yet. Always verify test command before first commit on a new bead.
Add `uv run pytest -x` to mental pre-commit checklist.
```

---

## Artifact Writing Checklists

### Trap Checklist

Before appending a trap:
- [ ] Is it generalizable? (Not "bug in fetchUser" but "missing None guard in input parsing")
- [ ] Does it prescribe avoidance? (Not just "this broke" but "do X instead")
- [ ] Is it stage-labeled? (TRAP [Stage N]: ...)

### Pattern Checklist

Before saving to open-brain:
- [ ] Is it reusable across projects? (scope: global) or project-specific? (scope: project:X)
- [ ] Does it have a confidence score? (0.0–1.0, default 0.8 for observed-once)
- [ ] Does it have a source? (`compound/<bead-id>`)
- [ ] Is it a positive pattern (do this) rather than a negative one (traps handle those)?

### Decision Checklist

Before creating a decision bead:
- [ ] Is it binding? (affects future work, not just this bead)
- [ ] Does the bead note include Context and Consequences?
- [ ] Is the label `decision` set?
- [ ] Is it not already documented in an existing decision bead? (check `bd list --label=decision`)

---

## Calibration Examples

### Too Specific (Don't Write)

```
TRAP: The `parse_invoice_date` function didn't handle timezones in the Collmex parser.
```

WHY: Instance-level. Not reusable. Future agent can't apply this to other code.

### Properly Generalized (Write)

```
TRAP: Date parsing functions that receive external input silently dropped timezone info.
Always normalize to UTC at the point of ingestion, not at the point of use.
```

---

## Integration with Session Close

`/compound` is an alternative to `/learnings-pipeline extract` in Step 7 of session-close.

Use `/compound` when:
- The bead was complex (3+ implementation cycles)
- There was a notable incident (bug that escaped to production, major pivot)
- You want structured Decision artifacts in beads (not just JSONL patterns)

Use `/learnings-pipeline extract` when:
- Quick session wrap-up, no major incidents
- Pattern density is low
- You want to extract from the full conversation history, not just one bead
