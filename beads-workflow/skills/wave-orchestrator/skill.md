---
name: wave-orchestrator
description: >-
  Orchestrate parallel implementation of multiple beads across cmux panes in dependency-aware
  waves. Use when implementing a whole feature area (eUeberweisung, eArztbrief, Medistar adapter),
  dispatching multiple beads at once, or running parallel cld -b sessions. MUST USE when user says
  "wave", "parallel beads", "implement all beads for X", "start the beads",
  or references implementing more than 2 beads at once. Also triggers on "cmux dispatch",
  "multi-bead", "wave orchestrator".
---

# Wave Orchestrator

Orchestrate parallel bead implementation across cmux panes. Takes a feature area or list of
bead IDs, sorts them into dependency waves, ensures preconditions (scenarios for features),
sets up cmux panes, dispatches `cld -b <id>` into each, and monitors until completion.

**Bundled scripts** (in `scripts/` relative to this skill):
- `wave-dispatch.sh` — Creates panes, names surfaces, dispatches `cld -b`, outputs wave config JSON
- `wave-status.sh` — Reads all surfaces in parallel, pattern-matches status, returns structured JSON
- `wave-completion.sh` — Quick check: all beads closed + all panes idle? Returns JSON + exit code

These scripts replace manual per-surface cmux calls. Use them instead of invoking cmux
directly for dispatch, monitoring, and completion checks.

## Arguments

`$ARGUMENTS`

| Pattern | Behavior |
|---------|----------|
| `<topic>` | Search beads for topic, present candidates, plan waves |
| `<id1> <id2> ...` | Use these specific bead IDs |
| `--dry-run` | Plan waves and show layout, don't dispatch |
| `--max-parallel=N` | Limit concurrent panes (default: 4) |
| `--skip-scenarios` | Don't check/generate scenarios for feature beads |

Examples:
```
/wave-orchestrator eUeberweisung
/wave-orchestrator mira-adapters-0al mira-adapters-n4r mira-adapters-0r0
/wave-orchestrator eArztbrief --max-parallel=3
/wave-orchestrator --dry-run Mahnung
```

---

## Phase 0: Bead Discovery

Goal: Find all beads that belong to the requested feature area.

### If specific bead IDs given

Validate each ID exists:
```bash
bd show <id>  # for each ID
```

### If topic/keyword given

Search broadly — feature areas often span multiple naming conventions:

```bash
bd list --status=open
bd list --status=in_progress
bd search "<topic>"
bd search "<alternate-spelling>"  # e.g. "ueberweisung" AND "Überweisung"
```

Present candidates as a numbered list with status, type, and title. Let the user confirm
which beads to include.

**Status flags** — flag these but don't auto-exclude (the user decides):
- `closed` — already done, usually skip
- `in_progress` — may already be running in another pane. If the user confirms inclusion,
  **do not dispatch** `cld -b` for these. Instead, locate the existing surface (search by
  bead ID in workspace surfaces) and adopt it into monitoring. Only dispatch if the user
  confirms the bead is not actively running elsewhere.

**Inclusion heuristics** (suggest, don't auto-decide):
- Same epic parent → likely belongs together
- Shared labels → likely belongs together
- Dependency chain → must be included if a dependent is included
- `blocked` status → include the blocker too, or flag it

---

## Phase 1: Dependency Analysis & Wave Planning

Build a dependency graph from `bd show <id>` for each selected bead. Extract:
- `blocked_by` → this bead waits for those
- `blocks` → those beads wait for this one

### Topological Sort into Waves

**Wave 1**: Beads with no unresolved dependencies (all blockers are either closed or not
in our set). These run first, in parallel.

**Wave 2**: Beads whose blockers are all in Wave 1. These start after Wave 1 completes.

**Wave N**: Continue until all beads are placed.

**Circular dependencies**: If detected, stop and report — the user needs to fix the
dependency graph before proceeding.

### Conflict Risk Assessment

Before finalizing waves, assess whether beads in the same wave are likely to modify the
same files. Every project has shared infrastructure files — routing tables, test setup,
app entry points, sync registries. Multiple beads adding new endpoints or features will
almost certainly touch these shared files.

**How to assess**: Look at each bead's endpoint/feature description. If multiple beads add
similar types of functionality (e.g. new API endpoints, new sync methods), they'll likely
touch the same infrastructure files. Read the project's CLAUDE.md or router/test files to
identify the specific shared hotspots.

**If >2 beads in a wave touch the same files**:
- Warn the user with specific file names
- Suggest sub-waves (e.g. 2 parallel, then 2, then 1) to reduce merge conflict surface
- If the user accepts the risk, proceed — but be prepared for merge conflicts
  (see `references/error-recovery.md`)

### Wave Table

Present the plan before executing:

```
## Wave Plan: eUeberweisung (6 beads)

| Wave | Bead | Type | Title | Depends on |
|------|------|------|-------|------------|
| 1 | mira-adapters-0al | task | KBV eUeberweisung Types | — |
| 1 | mira-adapters-doq | task | fhir-dental-de import | — |
| 2 | mira-adapters-n4r | task | Fachrichtung kodieren | 0al |
| 2 | mira-adapters-0r0 | task | ServiceRequest.reasonCode | 0al |

Max parallel: 4 | Waves: 2
Warning: Conflict risk — 0al, doq both modify pvs-router.ts
```

Wait for user confirmation before proceeding. If `--dry-run`, stop here.

### Parallel Limit

Default max 4 concurrent panes. Beyond 5, layout management becomes overhead and
resource contention increases (integration tests may compete for database connections,
file locks, or network ports). The user can override with `--max-parallel=N`.

If a wave has more beads than `max-parallel`, split the wave into sub-waves that respect
the limit.

---

## Phase 1.5: Scope Analysis (Compound Bead Detection)

Before dispatching, analyze each bead's scope to detect compound beads that are likely
to oscillate in review. Compound beads cover multiple orthogonal concerns and reliably
cause review ping-pong because fixing one dimension introduces regressions in another.

### Scope Signals

For each bead in the wave, check these signals:

| Signal | Weight | How to detect |
|--------|--------|---------------|
| **Compound title** | Strong | Title contains "and", "+", commas, or multiple verb phrases (e.g. "Fix X + refactor Y") |
| **Independent ACs** | Strong | Acceptance criteria can be satisfied without touching each other's code. If AC-1 and AC-3 modify different files/functions, they're independent → should be separate beads |
| **Multi-directory scope** | Medium | Description implies changes in 3+ unrelated directories or packages |
| **Historical oscillation** | Medium | Similar beads in the project previously had 3+ iterations or SCOPE-EXPAND (check `bd search` for related closed beads) |
| **Multiple verb phrases in description** | Weak | "Implement X, migrate Y, and update Z" |

### Detection Process

For each bead, spawn a **haiku-class subagent** to keep the analysis cheap and fast:

```
Agent(model="haiku", prompt="
  Analyze this bead for scope complexity:

  <bd show output>

  Questions:
  1. Does the title contain compound indicators (and, +, commas, multiple verbs)?
  2. Can each acceptance criterion be satisfied independently (different files/functions)?
  3. Does the description span 3+ unrelated modules or directories?

  If the bead covers 2+ orthogonal concerns, suggest a split with:
  - Sub-bead A: title, which ACs, which files
  - Sub-bead B: title, which ACs, which files
  - Dependencies between sub-beads (if any)

  If the bead is well-scoped (single concern), say: SCOPE OK.

  Keep response under 150 words.
")
```

Run these subagents in parallel (one per bead in the wave).

### Acting on Results

**If split recommended:**
1. Present the split suggestion to the user with the sub-bead breakdown
2. If user approves:
   ```bash
   bd create --title="<sub-bead-A title>" --description="<ACs for A>" --type=<type> --priority=<same>
   bd create --title="<sub-bead-B title>" --description="<ACs for B>" --type=<type> --priority=<same>
   bd dep add <sub-bead-B> <sub-bead-A>  # if B depends on A
   bd supersede <original-id> --with=<sub-bead-A>  # mark original as superseded
   ```
3. Re-run wave planning (Phase 1) with the new sub-beads replacing the original
4. If user rejects: proceed with the original bead but add an annotation:
   ```bash
   bd update <id> --append-notes="⚠ Compound scope detected — risk of review oscillation. Consider SCOPE-EXPAND after iteration 2 if review ping-pongs."
   ```

**If SCOPE OK:** proceed to Phase 2 without changes.

### Skip Conditions

Skip scope analysis for:
- Beads with only 1-2 acceptance criteria (too small to be compound)
- Type `bug` with a clear single root cause in the title
- Type `chore` (typically mechanical, low oscillation risk)

---

## Phase 2: Scenario Pre-Check

Before dispatching, every **feature** bead needs a `## Scenario` section in its description.
Without it, `cld -b` will start the bead-orchestrator which will immediately block with
"Missing Scenario". This wastes a pane and time.

**Exempt**: `type: task`, `type: bug`, `type: chore` — no scenario needed.

### Check

For each feature bead, run `bd show <id>` and look for `## Szenario` or `## Scenario`
(both spellings for backwards compatibility with existing beads).

### Generate Missing Scenarios

**Do NOT generate scenarios yourself.** Delegate to a subagent for each bead that needs
a scenario. This keeps the orchestrator's context lean and produces better scenarios
because each subagent can read package-specific CLAUDE.md files.

```
Agent(subagent_type="general-purpose", prompt="
  Read bd show <id> and the CLAUDE.md of the affected package.
  Generate a ## Scenario section following this template:

  ## Scenario
  **Precondition:** <What data/state must exist>
  **Action:** <What the user does>
  **Expected Result:** <What the system produces>
  ### Test Data
  <Seed data, fixtures, test inputs needed>
  ### Variants
  <States/variants to cover — not just the happy path>

  Write the scenario into the bead via:
  bd update <id> --description='<existing description + generated scenario>'
")
```

Run these subagents in parallel (one per bead). Present results to user for confirmation.

If `--skip-scenarios` is set, skip this phase entirely.

---

## Phase 3+4: Dispatch (using wave-dispatch.sh)

Instead of manually creating splits, naming surfaces, and sending commands one by one,
use the bundled dispatch script. It handles the full Phase 3 + Phase 4 sequence in one call:

```bash
SKILL_DIR="$(dirname "$(readlink -f "$0")")"  # or use the known skill path
./scripts/wave-dispatch.sh <bead-id1> <bead-id2> ... > /tmp/wave-config.json
```

Or with an explicit workspace:
```bash
./scripts/wave-dispatch.sh <bead-id1> <bead-id2> --workspace workspace:5 > /tmp/wave-config.json
```

The script:
1. Creates horizontal splits (`cmux new-split right`) with 3s delays between them
2. Renames each surface tab to `<short-id>-impl`
3. Dispatches `cld -b <bead-id>` to each surface
4. Outputs a wave config JSON to stdout (save this — it's the input for monitoring)

**Output format** (saved to `/tmp/wave-config.json`):
```json
{
  "dispatch_time": "2026-03-30T14:00:00",
  "workspace": "workspace:5",
  "beads": [
    {"id": "mira-adapters-0al", "surface": "surface:3"},
    {"id": "mira-adapters-doq", "surface": "surface:5"}
  ]
}
```

After dispatch, confirm to the user which beads were dispatched to which surfaces.

**Important**: Do NOT use `cld -br` — that's for review-only sessions. The dispatch script
uses `cld -b` which is the full implementation dispatch.

---

## Phase 5: Monitoring (using wave-status.sh)

Instead of reading each surface individually and parsing terminal output in-context,
use the bundled status script. It reads all surfaces in parallel, pattern-matches known
status indicators, cross-checks against `bd show`, and returns structured JSON.

### Running a Status Check

```bash
./scripts/wave-status.sh /tmp/wave-config.json
```

**Output format:**
```json
{
  "elapsed_minutes": 18,
  "beads": [
    {"id": "mira-0al", "surface": "surface:3", "status": "in_progress", "detail": "Running tests", "bd_status": "in_progress", "follow_up_beads": []},
    {"id": "mira-doq", "surface": "surface:5", "status": "done", "detail": "Shell idle", "bd_status": "closed", "follow_up_beads": []},
    {"id": "mira-n4r", "surface": "surface:7", "status": "in_review", "detail": "Review active (iteration 2/3)", "bd_status": "in_progress", "follow_up_beads": ["mira-fix-x3r"]}
  ],
  "all_done": false,
  "follow_up_beads": ["mira-fix-x3r"]
}
```

### Status Values

| Status | Meaning | Action |
|--------|---------|--------|
| `in_progress` | Active editing or testing | Continue monitoring |
| `in_review` | review-agent active | Almost done, keep watching |
| `session_close` | Session close running | Almost done, wait |
| `done` | Shell idle or bead closed in DB | Check CI pipeline before marking wave done |
| `pipeline_failed` | Session close completed but CI pipeline failed | Spawn fix agent — see below |
| `blocked` | Missing scenario | Generate scenario, resend |
| `failed` | Error/crash detected | See `references/error-recovery.md` |
| `unreachable` | Surface not found | See `references/error-recovery.md` |
| `unknown` | Can't determine status | Read surface manually for more context |

### Pipeline Check After Session Close

When a bead transitions from `session_close` to `done` (surface goes idle), check whether
the CI pipeline for the pushed commit passed **before** treating the bead as complete:

```bash
# Find the most recent run on main (session-close merges feature→main)
gh run list --branch main --limit 3 --json databaseId,status,conclusion,headSha,createdAt \
  | jq 'map(select(.status == "completed")) | .[0]'
```

**If conclusion is `success`**: bead is truly done, proceed.

**If conclusion is `failure` or `cancelled`**: mark bead as `pipeline_failed` and spawn a fix agent:

```
Agent(subagent_type="general-purpose", prompt="
  The CI pipeline failed after session-close for bead <id>.
  Branch: main, commit: <sha>

  Steps:
  1. Run: gh run view <run-id> --log-failed
     to identify which job/step failed.
  2. Read the relevant source files and fix the root cause.
  3. Commit the fix directly to main with a conventional commit message.
  4. Push to origin/main.
  5. Confirm the next pipeline run passes: gh run watch <new-run-id> --exit-status

  Do NOT close the bead — it stays open until the pipeline passes.
  Report: PIPELINE FIX RESULT: <PASSED|FAILED> — <short summary>
")
```

**Timing note**: Wait up to 2 minutes for the pipeline run to appear after the surface goes idle.
If no run appears, check whether the repo has CI configured (`ls .github/workflows/`). If no
CI config exists, treat the bead as done without a pipeline check.

### Monitoring Schedule

| Time after dispatch | Action |
|---------------------|--------|
| T+10 min | First check — catch immediate failures |
| T+15 min | Second check — most beads nearing mid-point |
| T+18 min | Third check — catch fast completions |
| T+20 min onwards | Every 3 min until wave completes |

**Use `run_in_background`** for the sleep between checks so the main agent stays
responsive for user questions.

### Status Updates

After each check, present the JSON output as a readable table to the user:

```
## Wave 1 Status (T+18min)

| Bead | Surface | Status | Detail |
|------|---------|--------|--------|
| 0al | surface:3 | in progress | Running tests |
| doq | surface:5 | done | Bead closed in database |
| n4r | surface:7 | in review | Review active (iteration 2/3) |

Follow-up beads detected: mira-fix-x3r
```

### When wave-status.sh Returns `unknown`

If a bead shows `unknown` status, fall back to manual inspection:
```bash
cmux read-screen --surface surface:<N> --scrollback --lines 50
```
Read the output yourself and determine the actual state.

### Sleep/Suspend Recovery

If all surfaces show **no change** between two monitoring cycles but processes are still
alive, the machine likely went to sleep. The agents resume automatically after wake.

**Rule**: Only declare a bead as "stuck" after **two consecutive identical checks** where
the screen output hasn't changed AND processes show no CPU usage. A single unchanged check
is normal (especially during long-running integration tests or sleep recovery).

---

## Phase 6: Wave Completion & Transition

### Quick Completion Check (using wave-completion.sh)

```bash
./scripts/wave-completion.sh /tmp/wave-config.json
echo $?  # 0 = all done, 1 = not yet
```

**Output format:**
```json
{
  "complete": false,
  "all_beads_closed": false,
  "all_surfaces_idle": true,
  "stragglers": [{"id": "mira-0al", "bd_status": "in_progress", "surface_idle": false}],
  "unclosed_follow_ups": [{"id": "mira-fix-x3r", "status": "open"}]
}
```

Use this for quick polling between full status checks. The exit code makes it easy to
use in a loop or conditional.

### Session Close — FORBIDDEN for the Wave Orchestrator

**The wave orchestrator must NEVER trigger `session close` or send `cmux send "session close"`.**

The bead-orchestrator handles the full lifecycle autonomously:
1. Implementation → Review (spawns `cld -br` in its own pane)
2. cmux-reviewer reviews, injects fixes, triggers `session close`
3. Session-close agent merges, tags, pushes, and closes the bead

The wave orchestrator **only observes** and waits until the pane is fully idle.

### Surface Reuse: FORBIDDEN

**Never reuse a surface for a new bead.** Even if a bead looks finished — the reviewer
process may still be running, session close may still be active, or background tasks
may still be pending.

For every new wave or bead dispatch: **always use `wave-dispatch.sh`** which creates
fresh surfaces. Never manually reuse surfaces from a previous wave.

### Follow-up Beads

The status and completion scripts automatically detect follow-up beads created during
implementation/review (by scanning for `Created issue:` in scrollback). When detected:

1. They appear in the `follow_up_beads` array of the status output
2. The completion script checks if they're closed before reporting wave complete
3. Report them in the status table to the user

No manual scanning needed — the scripts handle detection.

### Verify Wave Completion

After `wave-completion.sh` returns exit code 0:

```bash
git pull --no-rebase
git log --oneline -10  # Verify merges landed on main
```

### Start Next Wave

```bash
git pull --no-rebase
bd dolt pull
```

Then repeat from Phase 3+4 with `wave-dispatch.sh` for the next set of beads.

---

## Phase 7: Learnings Report

After each wave completes (all beads closed, all surfaces idle), generate a structured
learnings report BEFORE surfaces are cleaned up. The reviewer scrollback is the primary
data source and is lost once surfaces close.

### Data Collection (per bead)

For each completed bead, collect:

1. **Bead notes**: `bd show <id>` — close reason, iteration count, quality grade
2. **Reviewer findings** (if cmux-reviewer was used):
   ```bash
   # Read reviewer surface scrollback before it's cleaned up
   cmux read-screen --surface <reviewer-surface> --scrollback --lines 100
   ```
   Extract: BLOCKING findings (fixed), ADVISORY findings (deferred), Codex findings
3. **Implementation commits**: `git log --oneline <branch>` — what actually changed
4. **Follow-up beads created**: beads with `discovered-from: <bead-id>` in the wave

### Report Structure

The report focuses on **what was learned**, not what was done. Completion status is
secondary to architectural insights and process learnings.

```markdown
## Wave N — Learnings Report

### Architecture Insights
[Numbered. Each entry answers: What was previously invisible? Why is it visible now?
What's the consequence? Who found it (Codex/Opus/Sonnet)?]

1. **<topic>**: <insight>
   - Found by: <Codex adversarial / Opus review / Sonnet impl / verification-agent>
   - Consequence: <what changes because of this insight>

### Process Learnings
[Where did the multi-agent workflow catch something that would have slipped through?
Where did it create unnecessary work?]

- **Caught**: <what was caught, by which stage>
- **Overhead**: <where the process added cost without proportional benefit>

### Codex Adversarial Highlights
[If Codex was used: findings that were qualitatively different from Opus/Sonnet reviews.
These are often the most valuable — they reveal systematic issues.]

- <bead-id>: <finding summary>

### Bead Recommendations from Reviews
[Concrete next steps distilled from review findings, with source bead]

| Source | Recommendation | Type |
|--------|---------------|------|
| <bead> | <what to do next> | task/feature/refactor |

### Completion Table
[Per-bead summary — secondary to the sections above]

| Bead | Iterations | Grade | Key Finding |
|------|-----------|-------|-------------|
| <id> | <N> | <A/B/C> | <one-line summary> |

### CLAUDE.md Updates Made
[List any project CLAUDE.md changes made during this wave]
```

### Where to Store the Report

1. **User output**: Display the full report in the wave orchestrator conversation
2. **open-brain**: Save as a memory for cross-session recall:
   ```
   mcp__open-brain__save_memory({
     content: "<report content>",
     metadata: { tags: ["wave-report", "learnings", "<project-name>"], source: "wave-orchestrator" }
   })
   ```
3. **Bead notes**: For each closed bead, append a one-line summary referencing the wave report:
   ```bash
   bd update <id> --append-notes="Wave N report: <key learning for this bead>"
   ```

### Timing

Generate the report AFTER `wave-completion.sh` returns exit 0 but BEFORE starting the
next wave. The reviewer scrollback must still be accessible — if surfaces have already
been cleaned up, fall back to bead notes and git log (less rich but still useful).

### After All Waves

After all waves are complete, produce a final summary aggregating across waves:

```
## Wave Orchestration Complete

| Wave | Beads | Status |
|------|-------|--------|
| 1 | 0al, doq | all closed |
| 2 | n4r, 0r0 | all closed |

Total: 4 beads, 2 waves
Key insights across all waves: <2-3 bullet points>
Follow-up beads created: <count> (<list IDs>)
Remaining open beads for this area: <count or "none">
```

---

## Error Recovery

For all error scenarios, read `references/error-recovery.md`. It covers:

- Bead fails during implementation
- Reviewer disconnect (no impl surface)
- Merge conflicts during session close
- Session close collision between parallel beads
- Session close fails
- cmux pane becomes unresponsive

---

## Rules

- **Output language**: Respond in the user's language. The skill instructions are English but output should match the user.
- **Use the scripts**: Prefer `wave-dispatch.sh`, `wave-status.sh`, and `wave-completion.sh` over manual cmux calls. They're faster, produce structured output, and reduce context usage.
- **NEVER session close**: The wave orchestrator must never trigger or send `session close`. The bead-orchestrator/cmux-reviewer handles this autonomously.
- **NEVER reuse surfaces**: Always dispatch to fresh surfaces via `wave-dispatch.sh`.
- **Delegate scenarios**: Delegate scenario generation to subagents, not inline.
- **Check conflict risk upfront**: Before wave dispatch, check if beads will modify the same files. If so: max 2 parallel or use sub-waves.
- **Stuck = 2x identical**: A bead is only "stuck" after two consecutive identical status checks with no CPU usage. A single unchanged check is normal.
- **No time estimates**: Don't predict how long individual beads will take.
- **User confirms waves**: Never auto-dispatch without user approval.
- **Scenarios before dispatch**: Feature beads without scenarios waste pane time.
- **max 4-5 panes**: Beyond 5, layout overhead and resource contention become issues.
- **Pull between waves**: Always `git pull --no-rebase` + `bd dolt pull` between waves.
- **Don't monitor too early**: First check at T+10min, not T+1min.
- **Expect extra panes**: bead-orchestrators spawn their own review panes via `cld -br` — this is normal, don't intervene.
- **Reviewer intervention only on disconnect**: Only intervene when cmux communication between impl and reviewer demonstrably failed. Otherwise stay out.
