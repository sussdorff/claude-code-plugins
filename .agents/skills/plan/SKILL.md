---
description: Generate implementation plan with context, review, decisions, and test strategy
argument-hint: [TICKET-ID | issue description]
tags: project
timeout: 600000
---

# /plan - Interactive Planning Before Implementation

This command covers everything before writing code: gathering context, generating a plan, reviewing it, resolving questions, and defining the test strategy. The output is a plan document ready for `/impl`.

## Workflow Position

```
plan (interactive) -> impl (autonomous) -> "session close" (ship via agent)
```

## Modes

| Invocation | Mode |
|------------|------|
| `/plan <ticket-id or description>` | Single-bead mode (existing behavior) |
| `/plan --label <label>` | Batch planning mode (all open beads with label) |

If argument starts with `--label`, enter Batch Planning Mode (see Batch Orchestration below).
Otherwise, enter Single Bead Mode (existing Steps 0-7).

---

## Step 0: Scale-Adaptive Detection

Before gathering context, determine the task's complexity level to calibrate planning depth. See `standards/workflow/scale-adaptive.md` for full criteria.

### Quick Assessment

Scan the task description and any available ticket metadata for complexity signals:

| Signal | Level |
|--------|-------|
| "typo", "rename", "config change", single-file fix | **Level 0** -- Skip /plan, fix directly |
| 1-3 files, single module, clear fix/addition | **Level 1** -- Minimal plan (Steps 1-2 only, abbreviated) |
| Multi-file, cross-directory, needs decisions | **Level 2** -- Standard /plan (all steps) |
| New project, major architecture, multi-component | **Level 3** -- Extended /plan (all steps + persona analysis) |
| Cross-repo, multi-team, governance required | **Level 4** -- Full lifecycle /plan |

### Detection Output

Report the detected level and ask for confirmation:

```
Scale-Adaptive Detection: Level [N] ([Type])
Rationale: [Why this level was detected]

Proceed with Level [N] planning? (or specify --level=X to override)
```

### Level-Specific Flow

| Level | Steps Executed | Notes |
|-------|---------------|-------|
| 0 | None | Suggest `/impl` directly or manual fix |
| 1 | Steps 1-2 (abbreviated) | Skip independent review, skip test strategy if pattern is obvious |
| 2 | Steps 1-6 (full) | Standard flow |
| 3 | Steps 1-6 + Step 1.5 (persona analysis) | After context gathering, optionally run Analyst/PM/Architect perspectives. See `standards/workflow/planning-personas.md` |
| 4 | Steps 1-6 + Step 1.5 + cross-repo analysis | Level 3 flow plus impact analysis across repos |

---

## Step 0.5: Architecture Scout (pre-implementation check)

**Scale-adaptive**: Run for Level 2+ only. Skip for Level 0-1 (single-file fixes, typos, config changes).

### When to Run

After Scale-Adaptive Detection confirms Level 2+, spawn the architecture-scout agent before
gathering full context. The scout identifies architectural debt, missing ADRs, and vision
boundary violations early — when they are cheap to address.

### How to Spawn

```python
import os
scout_input = {
  "bead_id": "<ticket-id>",
  "bead_description": "<ticket description or user's input>",
  "touched_paths": ["<package-or-path-1>", "<package-or-path-2>"],
  "mode": "<advisor|gate from project config, default: advisor>",
  # CONFORMANCE_SKIP bypass: read env var here (before spawning) and pass it through
  "conformance_skip": os.environ.get("CONFORMANCE_SKIP") == "1"
}
Invoke the configured architecture-scout helper with `scout_input`.
```

**Determining `touched_paths`**: Extract package/directory mentions from the ticket
description, acceptance criteria, or the argument passed to `/plan`. If the ticket
references specific files or modules, include their parent package directory. If
uncertain, use an empty array (scout will scan all packages).

### Handling the Output

**If the project has no `docs/adr/` and no `vision.md`:**
The scout returns `CONFORM` with empty findings. Append the following note to the plan:

> No contracts declared yet — consider running `/project-context` first to document
> existing patterns and bootstrap your ADR library.

Continue to Step 1 normally.

**In advisor mode** (default):

1. Append the `## Coverage Matrix (architecture-scout)` section to the plan document
2. For any finding with `severity: "BLOCKING"`: add a DECIDE item to `## Developer Decisions`:

   ```markdown
   ### Q: Architecture Scout — BLOCKING: <rule>
   **Concern**: <concern from finding>
   **Source**: <source from finding>
   **Decision**: [Unresolved — resolve in Step 4]
   ```

3. For ADVISORY findings: append inline notes in the Coverage Matrix (no separate DECIDE item)
4. Continue to Step 1 (do NOT block the plan)

**In gate mode** (project config → `architecture-scout.mode: gate`):

- If the scout returns `status: VIOLATION` (BLOCKING findings exist):
  ```
  BLOCKED: architecture-scout reported N blocking finding(s) — see plan.md#coverage-matrix.
  Resolve the findings before proceeding with /plan.
  ```
  Exit `/plan`. Do not continue to Step 1.

- If `CONFORMANCE_SKIP=1` is set in the environment: pass `"conformance_skip": true` in the scout input (shown above); the scout will log a warning and continue as advisor mode.

- If the scout returns `status: CONFORM`: continue to Step 1 normally.

---

## Step 1: Gather Context

### Ticket/Issue Source Detection

Determine where the work item comes from (in priority order):

| Source | Detection | How to read |
|--------|-----------|-------------|
| Arguments | User provided description directly | Use as-is |
| Beads | `.beads/issues.jsonl` exists | `bd show TICKET_ID` |
| GitHub Issues | `.git/config` contains github.com | `gh issue view TICKET_ID` |
| GitLab Issues | `.git/config` contains gitlab | `glab issue view TICKET_ID` |
| Local ticket dir | `ticket/docs/summary.md` exists | Read ticket files directly |
| JIRA | Project has jira-handler | Use jira-handler if available |
| Manual | None of the above | Ask user for context |

### Context Priming

Read available context to understand the requirements:
- Ticket/issue description and acceptance criteria
- Project README for architecture overview
- Relevant source files mentioned in the ticket

### Issue Type Mapping

Extract the issue type and select plan template:

| Issue Type | Plan Template |
|------------|---------------|
| Bug, Defect, Fehler | Bug template (root cause + fix) |
| Story, Feature, Enhancement | Feature template (phased implementation) |
| Task, Chore, Aufgabe | Chore template (current -> desired state) |
| Sub-task | Inherit from parent or use chore |
| * (unknown) | Chore template |

## Step 2: Generate Plan

Research the codebase and create an implementation plan using the appropriate template.

### Approach Analysis (Brainstorming Gate)

Before committing to an implementation, present **2-3 approaches** with trade-offs:

```markdown
## Approaches Considered

### Approach A: [Name]
- **Description**: [How it works]
- **Pros**: [Benefits]
- **Cons**: [Drawbacks, risks]
- **Effort**: [Relative effort: low/medium/high]

### Approach B: [Name]
- **Description**: [How it works]
- **Pros**: [Benefits]
- **Cons**: [Drawbacks, risks]
- **Effort**: [Relative effort: low/medium/high]

### Recommendation: [Approach X]
**Rationale**: [Why this approach wins]
```

**Scale-adaptive**: For trivial changes (typo, config, single-line fix), skip the approach analysis. For anything involving design decisions, architectural choices, or multiple possible implementations, present options.

### Bug Plan Structure
```markdown
# Bug: <name>
## Bug Description / Problem Statement / Solution Statement
## Steps to Reproduce
## Root Cause Analysis
## Approaches Considered (if multiple fix strategies exist)
## Relevant Files
## Step by Step Tasks
## Validation Commands
```

### Feature Plan Structure
```markdown
# Feature: <name>
## Feature Description / User Story / Problem Statement / Solution Statement
## Approaches Considered
## Relevant Files
## Implementation Plan (Foundation -> Core -> Integration)
## Step by Step Tasks
## Testing Strategy (Unit / Integration / Edge Cases)
## Acceptance Criteria
## Validation Commands
```

### Chore Plan Structure
```markdown
# Chore: <name>
## Current State / Desired State
## Approaches Considered (if multiple strategies exist)
## Relevant Files
## Step by Step Tasks
## Validation Commands
```

All plans must include at minimum:
- Problem/Feature description
- Approaches considered (for non-trivial changes)
- Relevant files
- Step by step tasks (ordered, with granular structure — see below)
- Validation commands

### Granular Task Structure (Mandatory for Level 2+)

Each task in "Step by Step Tasks" must be **self-contained enough for a fresh subagent** to
complete independently. This means:

```markdown
### Task N: <descriptive title>

**Files:** `src/auth/service.ts`, `tests/auth/service.test.ts`
**Change:** Add token refresh logic to `AuthService.validateSession()`
**Red test:** Write test: "should refresh expired token and retry request"
**Green code:** Implement refresh in `validateSession()`, call `tokenStore.refresh()`
**Verify:** `npm test -- --grep "should refresh expired token"` → expects PASS
```

Required fields per task:
| Field | Purpose | Example |
|-------|---------|---------|
| **Files** | Exact paths the subagent needs to read/edit | `src/api/routes.ts` |
| **Change** | What changes, expressed as behavior | "Add PUT endpoint for user profile" |
| **Red test** | What failing test to write first (TDD) | "should return 400 when email invalid" |
| **Green code** | Minimal implementation to make test pass | "Validate email format in handler" |
| **Verify** | Exact command + expected outcome | `pytest tests/test_api.py::test_put_profile` → PASS |

**Scale-adaptive:** For Level 0-1, the task description alone is sufficient. For Level 2+,
all five fields are required. This granularity enables subagent-driven development where
each task can be dispatched to a fresh agent with zero context loss.

## Step 2.5: Break Analysis (Pre-Mortem)

Before the independent review, stress-test the plan with a targeted pre-mortem:

```markdown
## Break Analysis

### Assumptions
- What does this plan assume about existing code, APIs, or data structures?
- Which assumptions are verified vs. taken on faith?

### Fragile Points
- Where could a small change in requirements invalidate the approach?
- Which integration points are most likely to surprise us?

### Dependency Risks
- Are there external services, libraries, or APIs that could behave differently than expected?
- Are there race conditions, ordering issues, or state management risks?

### Hardest-to-Verify Criteria
- Which acceptance criteria are hardest to test or demonstrate?
- Are there MoC types that might not catch a subtle regression?
```

**Scale-adaptive:** Skip for Level 0-1. For Level 2+, include in the plan output. For Level 3+, expand with cross-component failure modes.

**Output:** Add as a `## Break Analysis` section in the plan document, directly after `## Approaches Considered`. Flag any items that should alter the plan or require upfront decisions.

## Step 3: Independent Review

Launch a separate agent to review the plan:

```
Invoke a separate plan-review helper if the harness provides one.

Prompt: "Review the implementation plan at [PLAN_PATH].
Read the ticket context at [CONTEXT_SOURCE].
Analyze for: completeness, technical feasibility, edge cases, testing strategy, open questions.
Append your review as '## Independent Review' section."
```

The review produces:
- Coverage Assessment
- Potential Issues
- Missing Considerations
- Questions for Developer
- Recommendation (Ready / Needs refinement / Blocked by questions)

## Step 4: Resolve Questions Interactively

For each open question from the Independent Review, ask the developer:

```
Ask the user directly with:
- question: The specific question
- header: Short context (e.g., "Edge case", "Scope", "Testing")
- options: 2-4 reasonable options based on codebase context
```

Document each decision:
```markdown
## Developer Decisions

### Q: [Original question]
**Decision**: [User's answer]
**Rationale**: [Brief explanation if provided]
```

If the review says "Blocked by questions", ALL questions must be resolved.

## Step 5: Define Test Strategy

### Framework Detection

Auto-detect the project's test framework:

| Detection Signal | Framework | Runner |
|-----------------|-----------|--------|
| `*.Tests.ps1` | Pester (PowerShell) | Remote Windows server via project test-runner |
| `*_spec.sh` | ShellSpec (Bash) | `shellspec -s /bin/bash` |
| `pytest.ini`, `conftest.py`, `pyproject.toml [tool.pytest]` | pytest | `uv run pytest` or `pytest` |
| `jest.config.*`, `__tests__/` | Jest | `npm test` or `npx jest` |
| `vitest.config.*` | Vitest | `npx vitest run` |
| `*_test.go` | Go testing | `go test ./...` |
| `Cargo.toml` + `#[test]` | Rust | `cargo test` |
| `spec/` (Ruby) | RSpec | `bundle exec rspec` |
| None detected | Manual | Ask user |

### Test Target Selection (if multi-system)

If the project involves deployment to multiple systems:
1. Identify available test targets from project configuration
2. Map file changes to platforms
3. Ask user which targets to use

### Create Test Plan

Add to the plan document:

```markdown
## Test Plan

### Test Framework
- **Unit Tests**: [Framework] (e.g., pytest, Jest, Pester)
- **Linter**: [Tool] (e.g., ruff, eslint, shellcheck)

### Target Systems (if applicable)
- **[Platform]**: [Target name]
- **Reason**: [Based on which files are modified]

### Unit Tests
| Test File | Framework | Command |
|-----------|-----------|---------|
| test_module.py | pytest | `uv run pytest tests/test_module.py` |

### Integration Tests (if applicable)
| Scenario | Target | Command |
|----------|--------|---------|
| [User behavior to validate] | [System] | [Command] |

### Expected Results
- **Before change**: [Current behavior / bug symptoms]
- **After change**: [Expected correct behavior]
```

## Step 6: Means of Compliance (MoC)

For each acceptance criterion in the bead or plan, suggest the appropriate verification method.

### MoC Type Selection

Map each acceptance criterion to one or more MoC types:

| MoC Type | When to Use |
|----------|-------------|
| `unit` | Function logic, calculations, data types, pure transformations |
| `e2e` | User workflows, UI interactions, multi-step flows |
| `integ` | API calls, service communication, DB queries |
| `review` | Architecture decisions, code quality, pattern adherence |
| `demo` | UI layout, visual behavior, responsive design |
| `doc` | Non-functional requirements, process changes, documentation updates |

### MoC Output

Add to the plan document:

```markdown
## Means of Compliance

| # | Acceptance Criterion | MoC | Planned Evidence |
|---|---------------------|-----|-----------------|
| 1 | [AK from bead/plan] | [unit/e2e/integ/review/demo/doc] | [Test name or verification method] |
| 2 | ... | ... | ... |
```

### Rules
- Every acceptance criterion MUST have at least one MoC type
- Prefer automated evidence (`unit`, `e2e`, `integ`) over manual (`review`, `demo`, `doc`)
- For config/doc-only changes: `doc` or `review` are valid MoC types
- The "Planned Evidence" column names the specific test function, file, or review step
- If a bead already has MoC defined (via comments), import it into the plan rather than re-generating

## Step 7: Finalize Plan

1. Update the `### Recommendation` to "Ready to implement"
2. Output confirmation:

```
Plan complete: <plan-file-path>

Summary:
- Type: [Bug/Feature/Chore]
- Questions resolved: X
- Test framework: [detected]
- Test targets: [list if applicable]
- MoC defined: [X criteria mapped]

Ready for /impl
```

## Error Handling

| Situation | Action |
|-----------|--------|
| No ticket/issue found | Ask user for context directly |
| Plan generation fails | Report error, suggest manual plan creation |
| Plan review fails | Continue without review (optional enhancement) |
| User skips questions | Warn that /impl may need to pause |
| No test framework detected | Ask user how to run tests |

## Batch Orchestration

When invoked with `--label <label>`, run these phases instead of Steps 0-7.

### Phase B0: Fetch and Preview

1. Run `bd list --label=<label> --status=open` to get all matching beads
2. If zero results: print "No open beads with label '<label>'" and exit
3. Display a numbered summary table of all beads (id, title, type, priority)
4. Ask the user: "Proceed with all N beads, or select a subset?"
   - Options: "All", "Select subset", "Cancel"
   - If subset: ask user for comma-separated numbers to include

### Phase B1: Cross-Bead Merge Detection

Before planning any bead, scan the full set for merge candidates:
- **Detection signals**: title similarity, shared file references in descriptions, one-blocks-the-other dependency
- For each candidate pair, ask the user:
  - "Merge into one bead"
  - "Keep separate"
  - "Skip both"
- **Merge action**: combine descriptions into the surviving bead via `bd update <surviving-id> --description="<merged>"`, close the other with `bd close <merged-id> --reason="Merged into <surviving-id>"`, remove from queue
- Show updated queue after merges

### Phase B2: Per-Bead Planning Loop

For each bead in sequence:

1. **Show overview**: Bead header with id, title, type, priority, and description excerpt

2. **Check for existing plan**: If `malte/plans/<id>.md` exists, ask the user:
   - "Re-plan from scratch"
   - "Skip this bead"
   - "View existing plan"

3. **Handle missing description**: If bead has no description, ask user to provide context or skip

4. **Autonomy pre-check** (key addition): Ask the user:
   - "What decisions or guidelines does the agent need to implement this autonomously?"
   - Options: "Provide decision rules", "No constraints — agent decides freely", "Skip this bead"
   - If decision rules provided: pre-populate the plan's "Developer Decisions" section

5. **Run Steps 0-7** with two modifications:
   - **Plan file path**: `malte/plans/<bead-id>.md` (not a random name)
   - **Autonomous-implementability mandate**: Step 3 (Independent Review) additionally checks: "Would any open question require the implementer to pause for human input?" Those are flagged as "BLOCKING for autonomous implementation" and MUST be resolved in Step 4 before moving to the next bead.

6. **Print confirmation**: `Plan saved: malte/plans/<bead-id>.md` → move to next bead

### Phase B3: Summary

After all beads are processed:

1. Display outcome table:

| Bead ID | Title | Outcome | Details |
|---------|-------|---------|---------|
| ... | ... | Planned | `malte/plans/<id>.md` |
| ... | ... | Merged | Into `<surviving-id>` |
| ... | ... | Skipped | User choice / no description |
| ... | ... | Failed | Error during plan generation |

2. Instruction: "Run `/impl <bead-id>` to implement a specific bead"

---

## Examples

```
# Plan from ticket ID
plan CH2-12345
plan #42
plan PROJ-123

# Plan from description
plan Fix the login timeout issue when session expires
plan Add CSV export to the reports page

# Plan from bead
plan claude-pa3

# Batch plan all beads with a label
plan --label tips
plan --label sprint-42
```
