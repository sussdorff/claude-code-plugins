---
name: compound
model: sonnet
description: >-
  Structured 4-stage retrospective for completed beads: Requirements vs Strategy, Strategy vs Execution, Iteration Review, Workflow Audit. Creates Trap/Pattern/Decision artifacts. Use when debriefing a bead, capturing session learnings, or running a compound retrospective.
disableModelInvocation: true
---

# Compound Retrospective

Structured 4-stage retrospective for completed beads. Produces three artifact types: **Traps**
(gotchas), **Patterns** (reusable structures), and **Decisions** (binding architectural choices).

## When to Use

- Debriefing a completed bead with notable complexity or incidents
- Capturing session learnings in structured form (alternative to `/learnings-pipeline extract`)
- Running a compound retrospective after a significant feature or multi-bead initiative
- User says "compound retro", "debrief bead", "retrospective", or "compound"

## Usage

```
compound --bead=<id>              # Analyze a specific bead
compound --bead=<id> --dry-run    # Print artifacts without saving
compound --bead=<id> --skip-decisions   # Skip creating decision beads
compound --bead=<id> --skip-patterns    # Skip saving patterns to open-brain
```

If `--bead` is omitted, ask the user which bead to retrospect before proceeding.

## The 4 Stages

Run these stages sequentially. Each stage surfaces specific artifact candidates.

<stage-1>
**Stage 1: Requirements vs Strategy**
Did the plan match the ticket/acceptance criteria?

- Fetch: `bd show <bead-id>` (acceptance criteria, title, description)
- Fetch: plan file from the harness plan directory if present
- Ask: Which acceptance criteria were addressed by the plan? Which were missed or misinterpreted?
- Artifacts: Traps (misread requirements), Decisions (scope choices made)
</stage-1>

<stage-2>
**Stage 2: Strategy vs Execution**
Did the implementation match the plan?

- Compare the plan with actual git commits: `git log --oneline` for the bead's changes
- Ask: What was built but not planned? What was planned but skipped? What was reordered?
- Artifacts: Patterns (what worked), Traps (what caused rework), Decisions (pivots made)
</stage-2>

<stage-3>
**Stage 3: Iteration Review**
What happened in follow-on bugfixes and refactors?

- Review bead comments/notes: `bd show <bead-id>` (notes, history)
- Review commits after the initial implementation
- Ask: What had to be fixed after "done"? What was refactored immediately? Was it avoidable?
- Artifacts: Traps (recurring patterns in bugs), Patterns (what made the fix clean)
</stage-3>

<stage-4>
**Stage 4: Workflow Audit**
Where did the process itself break down?

- Ask: Where was time lost to tooling, unclear ownership, or missing context?
- Ask: What would have made the session faster or safer?
- Artifacts: Traps (process gotchas), Patterns (workflow improvements), Decisions (tooling choices)
</stage-4>

## Artifact Types and Outputs

### Traps (gotchas to avoid)

Append to bead notes and optionally create as a bead with `trap` label:

```bash
bd update <bead-id> --append-notes="TRAP: <description>"
# For significant traps worth tracking independently:
bd create --title="[TRAP] <title>" --type=task --priority=3 --labels=trap
```

### Patterns (reusable structures)

Save via the open-brain memory connector:

- **title**: Pattern title (max 80 chars)
- **text**: Pattern description
- **type**: `learning`
- **project**: Derive from repo root
- **session_ref**: `compound-<bead-id>`
- **metadata**: `{"status": "open", "feedback_type": "pattern", "scope": "global", "confidence": 0.8, "source": "compound/<bead-id>", "tags": ["compound", "retrospective"]}`

Skip if `--skip-patterns` is set.

### Decisions (binding architectural choices)

Create as beads with `decision` label:

```bash
bd create --title="[DECISION] <title>" --type=decision --priority=2
bd update <new-id> --append-notes="Context: <why this decision was made>\nConsequences: <what it commits to>"
```

Skip if `--skip-decisions` is set.

## Optional Obsidian Output

If the `OBSIDIAN_VAULT` environment variable is set, also write a markdown summary:

```bash
mkdir -p "$OBSIDIAN_VAULT/Retrospectives"
# Write $OBSIDIAN_VAULT/Retrospectives/<bead-id>.md with all artifacts
```

Format: `## Stage N: <title>` sections, with artifacts listed as bullet points per stage.

## Dry Run

When `--dry-run` is set:
- Print all artifact candidates as formatted output
- Do NOT save to open-brain
- Do NOT create beads
- Do NOT write Obsidian files
- Prefix each artifact with `[DRY RUN] `

## Output Format

After all 4 stages, print a summary table:

```
## Compound Retrospective: <bead-id>

| Stage | Traps | Patterns | Decisions |
|-------|-------|----------|-----------|
| 1: Requirements vs Strategy | N | N | N |
| 2: Strategy vs Execution    | N | N | N |
| 3: Iteration Review         | N | N | N |
| 4: Workflow Audit           | N | N | N |
| **Total**                   | N | N | N |

Artifacts saved:
- Traps: appended to bead notes (+ N new trap beads created)
- Patterns: N entries saved to open-brain
- Decisions: N decision beads created
```

## Do NOT

- Do NOT skip a stage — every stage surfaces different artifact classes. WHY: requirements gaps and workflow failures are invisible if only code is reviewed.
- Do NOT create beads for every minor observation — only Decisions warrant independent beads. WHY: bead pollution makes the backlog unusable.
- Do NOT write patterns without a `source` field. WHY: provenance is required for deduplication in the learnings pipeline.
- Do NOT invent artifacts — only record what actually happened in the bead. WHY: fabricated retrospectives erode trust in the whole system.
- Do NOT run without `--bead=<id>` silently. WHY: the retrospective must be scoped to a specific bead to be meaningful.

## Resources

- `references/stages.md` — Detailed per-stage guidance with examples and question banks
- `learnings-pipeline` — Learnings pipeline for reviewing extracted patterns
- `beads:decision` — Beads decision management skill
