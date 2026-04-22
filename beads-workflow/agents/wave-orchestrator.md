---
name: wave-orchestrator
description: >-
  Orchestrate parallel implementation of multiple beads across cmux panes in dependency-aware
  waves. Use when implementing a whole feature area (eUeberweisung, eArztbrief, Medistar adapter),
  dispatching multiple beads at once, or running parallel cld -b sessions. MUST USE when user says
  "wave", "parallel beads", "implement all beads for X", "start the beads",
  or references implementing more than 2 beads at once. Also triggers on "cmux dispatch",
  "multi-bead", "wave orchestrator".
tools: Bash, Read, Agent
model: sonnet
---

# Wave Orchestrator

Orchestrate parallel bead implementation across cmux panes. Takes a feature area or list of
bead IDs, sorts them into dependency waves, ensures preconditions (scenarios for features),
sets up cmux panes, dispatches `cld -b <id>` into each, and monitors until completion.

**Bundled scripts** (in `scripts/` relative to the wave-orchestrator skill):
- `wave-dispatch.sh` — Creates panes, names surfaces, dispatches `cld -b`, outputs wave config JSON
- `wave-status.sh` — Reads all surfaces in parallel, pattern-matches status, returns structured JSON
- `wave-completion.sh` — Quick check: all beads closed + all panes idle? Returns JSON + exit code
- `wave-lock.sh` — Single-instance guard: prevents two wave orchestrators from running concurrently

These scripts replace manual per-surface cmux calls. Use them instead of invoking cmux
directly for dispatch, monitoring, and completion checks.

**Finding scripts:** Locate them via:
```bash
find ~/.claude/skills -name "wave-dispatch.sh" 2>/dev/null | head -1
find . -path "*/wave-orchestrator/scripts/wave-dispatch.sh" 2>/dev/null | head -1
```

## Arguments

`$ARGUMENTS`

| Pattern | Behavior |
|---------|----------|
| `<topic>` | Search beads for topic, present candidates, plan waves |
| `<id1> <id2> ...` | Use these specific bead IDs |
| `--dry-run` | Plan waves and show layout, don't dispatch |
| `--max-parallel=N` | Limit concurrent panes (default: 4) |
| `--skip-scenarios` | Don't check/generate scenarios for feature beads |
| `--skip-review` | Skip architecture review (Phase 1.5b) for all beads. Logged to audit. |
| `--skip-wave-review` | Skip wave-level structural review (Phase 1.25). Logged per-bead to notes. |
| `--skip-integration-check` | Skip Phase 6.5 integration-verification (cross-bead invariant check after final wave) |

Examples:
```
/wave-orchestrator eUeberweisung
/wave-orchestrator mira-adapters-0al mira-adapters-n4r mira-adapters-0r0
/wave-orchestrator eArztbrief --max-parallel=3
/wave-orchestrator --dry-run Mahnung
```

---

## Phase 0.5: Single-Instance Lock

Before doing any work, acquire the wave-orchestrator lock to prevent two instances from
running concurrently. The lock is stored at `$MAIN_REPO_ROOT/.wave-orchestrator.lock`.

### Acquiring the lock

```bash
# Locate wave-lock.sh
WAVE_LOCK_SH=$(find ~/.claude/skills -name "wave-lock.sh" 2>/dev/null | head -1)
if [[ -z "$WAVE_LOCK_SH" ]]; then
  WAVE_LOCK_SH=$(find . -path "*/wave-orchestrator/scripts/wave-lock.sh" 2>/dev/null | head -1)
fi

MAIN_REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "$HOME")
LOCK_FILE="$MAIN_REPO_ROOT/.wave-orchestrator.lock"

# Derive a wave_id for this session (used in error messages)
WAVE_ID="wave-$(date -u +%Y%m%d-%H%M%S)"

# Acquire: fail-fast if another live orchestrator holds the lock
bash "$WAVE_LOCK_SH" acquire "$LOCK_FILE" "$WAVE_ID" "${CMUX_SURFACE:-unknown}"
```

**Fail-fast behavior:**
- If another live orchestrator holds the lock → exit immediately with:
  ```
  ERROR: Wave orchestrator already running (wave_id: ..., surface: ...).
  Do NOT start another — use beads-workflow:wave-monitor to watch progress.
  ```
- If lock file exists but holder PID is dead → warn, auto-clear, proceed.
- If no lock → acquire immediately, continue to Phase 0.

### Releasing the lock

Release on clean exit (after Phase 7 completes or on user-requested abort):

```bash
bash "$WAVE_LOCK_SH" release "$LOCK_FILE"
```

Use a bash trap to ensure release even on unexpected exit:

```bash
trap 'bash "$WAVE_LOCK_SH" release "$LOCK_FILE" 2>/dev/null || true' EXIT
```

### Status check

To inspect whether a wave is running without acquiring:

```bash
bash "$WAVE_LOCK_SH" status "$LOCK_FILE"
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

### Dispatch Mode Classification

During wave planning, classify each bead's dispatch mode. For each bead:

```bash
EFFORT=$(bd show <id> --json | jq -r '.metadata.effort // ""')
TYPE=$(bd show <id> --json | jq -r '.type // ""')
```

**If `EFFORT` is empty**, do NOT default to `full`. Instead, estimate the effort first
(see "Effort Estimation for Unset Beads" below), then apply the table.

| Effort | Type | Mode |
|--------|------|------|
| `micro`, `small` | `bug`, `chore`, `task` | **quick** (`cld -bq`) |
| `medium`, `large`, `xl` | any | **full** (`cld -b`) |
| any | `feature` | **full** (`cld -b`) |

Store the mode per bead — it's used in the Wave Table display and in Phase 3+4 dispatch.

### Effort Estimation for Unset Beads

When a bead has no `effort` field set, spawn a **haiku-class subagent** per bead to
estimate effort before classification. Run all estimations in parallel.

```
Agent(model="haiku", prompt="
  Estimate the implementation effort for this bead. Read the title, description,
  and acceptance criteria carefully.

  <bd show output>

  Effort scale:
  - micro (XS): 1 file change, < 30 lines, no logic branches, no test changes needed
  - small (S): 2-5 files, < 100 lines total, straightforward logic, minimal test changes
  - medium (M): 5-15 files, non-trivial logic, requires tests/schema changes, or unclear scope
  - large (L): 15+ files, architectural impact, significant test coverage needed
  - xl (XL): multiple subsystems, migration required, high coordination cost

  Answer ONLY: micro | small | medium | large | xl
  Then one sentence justification.
")
```

After estimation, set the effort on the bead so it's visible in future sessions:

```bash
bd update <id> --metadata='{"effort": "<estimated>"}'
```

Use the estimated value in the dispatch mode table. Show the estimated effort in the
Wave Table with a `*` marker (e.g. `S*`) to indicate it was auto-estimated, not set
by the user.

### Wave Table

Present the plan before executing. The **Mode** column shows quick vs full routing:

```
## Wave Plan: eUeberweisung (6 beads)

| Wave | Bead | Type | Effort | Mode | Title | Depends on |
|------|------|------|--------|------|-------|------------|
| 1 | mira-adapters-0al | task | M | full | KBV eUeberweisung Types | — |
| 1 | mira-fix-x3r | bug | XS | quick | Fix null check in router | — |
| 1 | mira-adapters-doq | task | S* | quick | fhir-dental-de import | — |
| 2 | mira-adapters-n4r | task | M* | full | Fachrichtung kodieren | 0al |
| 2 | mira-adapters-0r0 | task | S | quick | ServiceRequest.reasonCode | 0al |

Max parallel: 4 | Waves: 2 | Quick: 3 | Full: 2
* = effort auto-estimated (not set in bead metadata)
Warning: Conflict risk — 0al, doq both modify pvs-router.ts
```

Quick-fix beads typically complete faster (no plan gate, no UAT, 2 review iterations max).
This is visible in monitoring — quick-fix surfaces show `<id>-qf` labels.

**Pane budget:** All beads use 1 pane each. Both full and quick-fix run their Codex
review inline (single-pane model). Factor this into `max-parallel` calculations:
a wave of 2 full + 2 quick needs 4 panes.

Wait for user confirmation before proceeding. If `--dry-run`, stop here.

### Parallel Limit

Default max 4 concurrent panes. Beyond 5, layout management becomes overhead and
resource contention increases (integration tests may compete for database connections,
file locks, or network ports). The user can override with `--max-parallel=N`.

If a wave has more beads than `max-parallel`, split the wave into sub-waves that respect
the limit.

---

## Phase 1.25: Wave Structural Review

Before scope analysis, run a cross-bead structural review to catch wave-level defects
(dependency-ordering errors, ownership collisions, lifecycle contradictions, validation
gaps) that single-bead review cannot see. This phase prevents expensive review
oscillation AFTER dispatch.

**Initialize at the start of this phase (before any skip-path exits):**
```bash
PHASE_125_ARCH_FINDINGS=""
```
This ensures the variable is always defined regardless of which exit path fires.

**Skip if `--skip-wave-review` is set.** Log per bead:
```bash
for id in <all bead IDs in wave>; do
  bd update "$id" --append-notes="Wave review skipped (--skip-wave-review flag). User: $(whoami), $(date -u +%Y-%m-%dT%H:%M:%SZ)"
done
```
Then exit Phase 1.25 (return to Phase 1.5 with `$PHASE_125_ARCH_FINDINGS` empty).

**Skip silently if the wave has only 1 bead** (no cross-bead invariants to check).
Exit Phase 1.25 immediately with `$PHASE_125_ARCH_FINDINGS` empty.

### Spawning the Wave-Reviewer Subagent

Spawn a general-purpose subagent. The subagent must call `codex exec --sandbox read-only`
directly via Bash (NOT `/codex`, NOT `/codex:rescue`). The subagent returns a structured
JSON findings report.

```
Agent(subagent_type="general-purpose", prompt="
  ## Wave Structural Review

  Review these beads as a wave candidate for cross-bead structural defects.

  ## Bead IDs to review
  <list of bead IDs>

  ## Instructions
  1. Run `bd show <id>` for each bead to load its title, description, ACs, deps.
  2. Check if `codex` is available: `command -v codex`
     - If YES: run the review via codex (see below).
     - If NO, or codex exits non-zero for ANY reason (not found, runtime error,
       **timeout (exit 124)**): perform the review yourself using Sonnet logic
       (see wave-reviewer SKILL.md for checklist) and set codex_fallback: 'sonnet'.

  ## Using codex exec (when available)

  Run with a hard timeout so a stalled codex cannot masquerade as a clean
  \"no findings\" review (a false-green). Exit 124 from `timeout` is treated
  identically to any other non-zero codex exit and triggers the Sonnet fallback.

  ```bash
  timeout 300 codex exec --sandbox read-only --model o3 '<prompt with bead data>'
  ```

  The prompt must instruct codex to return ONLY valid JSON matching this schema:

  ```json
  {
    \"verdict\": \"Structurally ready | Not ready for dispatch\",
    \"reviewed_at\": \"<ISO-8601 UTC>\",
    \"reviewed_beads\": [\"<id1>\", \"<id2>\"],
    \"findings\": [
      {
        \"bead_ids\": [\"<id>\"],
        \"severity\": \"HIGH | MEDIUM | LOW\",
        \"category\": \"fundamental | lokal | ac_minor | bead_quality | architecture | info\",
        \"finding\": \"<specific structural defect>\",
        \"recommendation\": \"<minimal fix>\"
      }
    ],
    \"codex_exit\": 0,
    \"codex_fallback\": null
  }
  ```

  Severity definitions:
  - HIGH + fundamental: Wave-redesign required (bead-split, dependency loop, lifecycle
    contradiction) — cannot dispatch without user decision
  - HIGH + lokal: Locally fixable (missing dep edge, wrong ownership) — fixable via
    bd update with user confirmation
  - MEDIUM: AC-minor issues, bead quality < B, small inconsistencies — auto-fixable
  - LOW / info: Structurally sound, no action required

  If `codex exec` exits non-zero for ANY reason (not found, error, **timeout
  (exit 124)**), capture the exit code and set:
  - codex_fallback: 'sonnet'
  - codex_exit: <actual exit code>
  Then perform the review yourself using Sonnet (load wave-reviewer SKILL.md logic) and
  produce the same JSON schema.

  ## Output
  Return ONLY the JSON object (no surrounding prose).
")
```

### Findings Triage

After the subagent returns the JSON findings report, parse and triage by severity.

**If `codex_fallback: 'sonnet'` in the JSON**, log to all wave bead notes:
```bash
bd update <id> --append-notes="Wave review: codex_fallback=sonnet, codex_exit=<N>"
```

**Process findings in this order: HIGH-fundamental → HIGH-lokal → MEDIUM → LOW**

#### HIGH-fundamental (stop + user dialog)

For each HIGH-fundamental finding — halt immediately and present to the user:

```
## Wave Review — BLOCKED: Structural Issue

Finding: <finding text>
Bead(s): <bead_ids>
Recommendation: <recommendation>

Options:
  A) Accept recommendation (split bead / restructure wave)
  B) Override and continue (logged to bead notes)
```

**In `--dry-run` mode:** Show the finding and options but do NOT create beads or make any
bd updates — this applies to BOTH path A (bd create + bd supersede) AND path B
(bd update --append-notes). No writes of any kind are performed in dry-run.

If user chooses A (accept):
- For bead-split: create sub-beads and supersede original:
  ```bash
  bd create --title="<sub-bead-A>" --type=<type> --priority=<priority>
  bd create --title="<sub-bead-B>" --type=<type> --priority=<priority>
  bd dep add <sub-bead-B> <sub-bead-A>  # if B depends on A
  bd supersede <original-id> --with=<sub-bead-A>
  ```
- Re-run Phase 1 with the new bead set
- Return to Phase 1.25 with updated wave

If user chooses B (override):
```bash
bd update <id> --append-notes="Wave review HIGH-fundamental override by user: <finding summary>. $(date -u +%Y-%m-%dT%H:%M:%SZ)"
```
Proceed to next finding. (In `--dry-run` mode: do NOT apply the `bd update --append-notes`
override log either — dry-run suppresses all writes.)

#### HIGH-lokal (user confirmation + apply)

For each HIGH-lokal finding — present the proposed fix and await confirmation:

```
## Wave Review — HIGH Finding (locally fixable)

Finding: <finding text>
Bead(s): <bead_ids>
Proposed fix: <recommendation (e.g. `bd dep add demo-epic-b demo-epic-c`)>

Apply this fix? [Y/N]
```

If confirmed:
```bash
# Apply the recommended fix (e.g. add dependency edge)
bd dep add <id1> <id2>
# or
bd update <id> --append-notes="<fix applied>"
```

In `--dry-run` mode: Show the finding and proposed fix, do NOT apply.

#### MEDIUM (auto-fix + summary)

For all MEDIUM findings — apply via `bd update` directly:

```bash
bd update <id> --append-notes="Wave review MEDIUM fix: <finding summary>"
# For ac_minor: if description improvement is needed, update the description field
# bd update <id> --description="<improved description>"
```

After all MEDIUM fixes, show a summary:
```
## Applied Wave Review Fixes (MEDIUM)
- <bead-id>: <what was fixed>
- <bead-id>: <what was fixed>
```

In `--dry-run` mode: Show what would be fixed but do NOT apply.

#### LOW / verdict "Structurally ready"

No action required. Proceed to Phase 1.5.

### Re-Review Loop (max 1)

If ANY of the following conditions are true, trigger exactly ONE re-review:
- HIGH-lokal finding was confirmed and applied
- MEDIUM finding was auto-applied
- HIGH-fundamental finding was overridden by the user (path B)

This ensures the re-review safety net always fires after user override decisions, not
only after programmatic fixes.

Re-spawn the wave-reviewer subagent with the same prompt but updated bead data.

If the second-pass verdict is still `Not ready for dispatch`:
```
## Wave Review — Second Pass: Still Not Ready

The following issues remain unresolved after applying fixes:
<second-pass findings>

Options:
  A) Continue anyway (logged to notes)
  B) Abort dispatch
```

Do NOT trigger a third review. The orchestrator does not loop indefinitely.

### Phase 1.5b Context Handoff

After Phase 1.25 completes (regardless of verdict), extract all findings with
`category: "architecture"` from the JSON report. Pass these to Phase 1.5b's
Architecture Council prompt as pre-existing context:

```
### Phase 1.25 Architecture Findings (do not re-review these)
<verbatim architecture findings from Phase 1.25 JSON>
```

This prevents Phase 1.5b from redundantly re-reviewing structural issues already
surfaced by Phase 1.25. Store the architecture findings in a variable for injection
into Phase 1.5b.

### JSON Output Schema

The JSON contract that the codex invocation must return (documented for wave-reviewer
subagent prompt construction):

```json
{
  "verdict": "Structurally ready | Not ready for dispatch",
  "reviewed_at": "<ISO-8601 UTC>",
  "reviewed_beads": ["<bead-id>", "..."],
  "findings": [
    {
      "bead_ids": ["<bead-id>"],
      "severity": "HIGH | MEDIUM | LOW",
      "category": "fundamental | lokal | ac_minor | bead_quality | architecture | info",
      "finding": "<specific structural defect>",
      "recommendation": "<minimal fix command or description>"
    }
  ],
  "codex_exit": 0,
  "codex_fallback": null
}
```

Fields:
- `verdict`: Overall wave readiness assessment
- `reviewed_beads`: All bead IDs that were reviewed
- `findings`: Empty array if verdict is "Structurally ready"
- `codex_exit`: Exit code from `codex exec` (0 = success, non-zero = error)
- `codex_fallback`: `null` if codex ran successfully, `"sonnet"` if Sonnet fallback was used

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
   bd update <id> --append-notes="Compound scope detected — risk of review oscillation. Consider SCOPE-EXPAND after iteration 2 if review ping-pongs."
   ```

**If SCOPE OK:** proceed to Phase 2 without changes.

### Skip Conditions

Skip scope analysis for:
- Beads with only 1-2 acceptance criteria (too small to be compound)
- Type `bug` with a clear single root cause in the title
- Type `chore` (typically mechanical, low oscillation risk)

---

## Phase 1.5b: Architecture Review (Design-Doc Gate)

After scope analysis (Phase 1.5), assess each bead for architectural complexity. Beads
that involve design decisions (boundaries, state machines, API contracts) get a structured
architecture review BEFORE implementation — preventing costly review oscillation.

**Skip this phase if `--skip-review` is set.** Log the skip:
```bash
bd update <id> --append-notes="Architecture review skipped (--skip-review flag). User: $(whoami), $(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

### Phase 1.25 Context

If Phase 1.25 found any `architecture`-category findings, they are passed in via
`$PHASE_125_ARCH_FINDINGS`. Inject these into the Architecture Council prompt under
`### Phase 1.25 Architecture Findings`. The council should NOT re-review these findings
but may reference them when assessing the beads.

If `$PHASE_125_ARCH_FINDINGS` is empty (no architecture findings from Phase 1.25),
omit this section from the council prompt.

### Signal Detection

Run the bundled detection script on all beads in the current wave:

```bash
./scripts/arch-signal-detect.sh <bead-id1> <bead-id2> ... > /tmp/arch-signals.json
```

The script outputs a JSON array with per-bead scores:
```json
[
  {"id": "mira-0al", "title": "...", "score": 9, "verdict": "REVIEW_YES", "signals": [...]},
  {"id": "mira-doq", "title": "...", "score": 2, "verdict": "REVIEW_NO", "signals": []},
  {"id": "mira-n4r", "title": "...", "score": 4, "verdict": "REVIEW_MAYBE", "signals": [...]}
]
```

**Verdicts:**
- `REVIEW_YES` (score >= 6): Architecture Council is triggered
- `REVIEW_MAYBE` (score 3-5): Haiku fallback classifies (see below)
- `REVIEW_NO` (score < 3): No review needed
- Bug/chore beads are auto-skipped (score 0)

### Haiku Fallback for REVIEW_MAYBE

For beads with `REVIEW_MAYBE`, spawn a haiku-class subagent to make the final call:

```
Agent(model="haiku", prompt="
  Read this bead description and decide: does this bead involve architectural decisions
  that should be reviewed before implementation?

  Bead: <bd show output>
  Signal score: <score> (threshold is 6, this bead scored <score>)
  Matched signals: <signals list>

  Additional check: Does this bead involve external authority catalogs (medical codes,
  legal registries, financial identifiers) that would require a dedicated scope without
  adapter-prefix? If yes, lean toward REVIEW_YES regardless of score.

  Answer ONLY: REVIEW_YES or REVIEW_NO with a one-sentence reason.
")
```

Run these in parallel (one per REVIEW_MAYBE bead). Fast and cheap.

**Note on canonical-catalog coverage:** The Haiku fallback only applies to `REVIEW_MAYBE` beads
(score 3-5). Low-scoring beads (score < 3) that involve catalog work bypass both checks.
For epic-level catalog gaps, rely on Phase 6.5 Integration-Verification as the backstop.

### Architecture Council Execution

For all beads with final verdict `REVIEW_YES`, run the Architecture Council.

**Model**: Use `architecture_review.council` from `model-strategy.yml` (default: opus).
This is different from the standard /council which uses haiku — architecture decisions
need deeper reasoning.

**Council roles** are loaded from `council-roles.yml` under the `architecture` profile:
1. **Architect** — Boundaries, interfaces, extensibility, dependency direction
2. **Operations** — Failure modes, monitoring, rollback, deployment risks
3. **Reviewer** — Testing strategy, edge cases, regression risks
4. **Integration** — Cross-bead dependencies, shared infrastructure, migration

**Execution**: If multiple beads need review, run **parallel councils** (one per bead).
Each council runs 4 sequential agents internally.

```
# For each REVIEW_YES bead, spawn in parallel:
Agent(subagent_type="general-purpose", model="opus", prompt="
  Du fuehrst ein Architecture Council Review fuer dieses Bead durch.

  ## Bead
  <bd show output>

  ## Rollen (architecture profile)
  <4 roles from council-roles.yml>

  ## Canonical-Catalog-Detection (Pre-Check vor den Rollen)
  Bevor die Review-Runden starten, pruefe:

  **Schritt 1 — Domain identifizieren:**
  Welche Fachdomaene betrifft dieses Bead?
  (Medical, Legal, Finance, Logistics, Identity, oder andere)

  **Schritt 2 — Externe Autoritaeten pruefen:**
  Existieren in dieser Domain kanonische Referenzkataloge externer Autoritaeten?

  Bekannte Beispiele:
  - Medical: KBV-Schluessel, DIMDI-Kataloge, ICD (WHO), LOINC, SNOMED CT, IFA-Artikelstamm
  - Legal: Gesetzessammlungen (BGBl, EUR-Lex), Gerichtsregister
  - Finance: IBAN/BIC (SWIFT), ISIN (ISO 6166), MCC-Codes, LEI
  - Logistics: UN/LOCODE, HS-Codes (WCO), EAN/GTIN
  - Identity: EIN, ORCID, GLN
  - (Fuer andere Domains: analoge Muster anwenden)

  Falls KEINE externen Kataloge existieren: kurz begruenden und zu Schritt 3 uebergehen.

  **Schritt 3 — Universal-Scope-Pruefung:**
  Falls externe Kataloge existieren:
  - Brauchen sie einen eigenen Scope OHNE adapter-prefix? (d.h. eine universal-Kategorie?)
  - Ist dieser Scope in der vorgeschlagenen Architektur bereits vorgesehen?
  - Falls NICHT vorgesehen: CRITICAL-Finding eintragen:
    \"Fehlender Universal-Scope fuer <Katalog-Name>: Kanonische Referenzdaten benoetigen
     einen eigenstaendigen Scope ohne adapter-prefix, damit alle Adapter denselben
     Referenz-Datensatz nutzen.\"

  Eintrag in Findings-Tabelle (Zeile 0, vor den Rollen-Findings):
  | 0 | INFO/CRITICAL | Pre-Check | Canonical-Catalog | <Ergebnis> | <Empfehlung> |

  ## Instruktionen
  Fuehre 4 Reviews sequenziell durch (jeder Agent sieht vorherige Kritiken).
  Jeder Agent: max 1500 Zeichen, NUR Findings, kein Prozess.
  Output-Format: COUNCIL-REVIEW: [Rollenname] + Findings + Staerken (max 2).

  Konsolidiere am Ende in eine Findings-Tabelle:
  | # | Severity | Agent | Thema | Finding | Empfehlung |

  Letztes Token: COUNCIL_BLOCKED: true/false

  ## Design Doc
  Schreibe nach dem Review ein Design-Doc als temporaere Datei:
  /tmp/arch-design-<bead-id>.md

  Das Design-Doc enthaelt:
  1. Current State: Wie funktioniert das System heute?
  2. Problem: Was ist falsch / was fehlt?
  3. Recommendation: Welcher Ansatz und warum
  4. Boundary Decisions: Welches Modul besitzt welche Verantwortung
  5. Council Findings: Konsolidierte Tabelle
  6. COUNCIL_BLOCKED Status

  WICHTIG: Die Datei ist temporaer und wird NICHT committed.
  Bei grundsaetzlichen Architekturentscheidungen: empfehle ein separates ADR-Bead.
")
```

### Presenting Results

After all councils complete, present results inline in the wave overview:

```
## Architecture Review Results

| Bead | Score | Verdict | Findings | Status |
|------|-------|---------|----------|--------|
| mira-0al | 9 | REVIEW_YES | 2C, 1W | COUNCIL_BLOCKED |
| mira-n4r | 4→YES | REVIEW_YES (Haiku) | 0C, 2W | OK |
| mira-doq | 2 | REVIEW_NO | — | skipped |

BLOCKED beads: mira-0al (2 CRITICAL findings)
Design docs: /tmp/arch-design-mira-0al.md, /tmp/arch-design-mira-n4r.md
```

**If any bead is COUNCIL_BLOCKED:**
1. Show the CRITICAL findings to the user
2. Ask: "Trotzdem dispatchen? (Escape Hatch)" or "Findings zuerst adressieren?"
3. If user chooses escape hatch, log:
   ```bash
   bd update <id> --append-notes="Architecture Council BLOCKED but user overrode. Findings: <summary>. $(date -u +%Y-%m-%dT%H:%M:%SZ)"
   ```

**If no beads are blocked:** proceed to Phase 2 automatically.

### Design Doc Lifecycle

The design doc (`/tmp/arch-design-<bead-id>.md`) is:
- **Written** by the Architecture Council agent
- **Read** by the bead-orchestrator when it starts implementation (if the file exists)
- **Deleted** automatically when the worktree is cleaned up after session close
- **NOT committed** to git — these are implementation-level details, not persistent architecture

If the council identifies fundamental architectural decisions that affect multiple beads:
- Recommend creating an ADR (Architecture Decision Record) as a separate bead
- The ADR bead should block the implementation beads

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
use the bundled dispatch script. It handles the full Phase 3 + Phase 4 sequence in one call.

### Routing: Full vs Quick-Fix

Before dispatching, classify each bead for routing:

```bash
# For each bead in the wave, check effort and type
EFFORT=$(bd show <id> --json | jq -r '.metadata.effort // ""')
TYPE=$(bd show <id> --json | jq -r '.type // ""')
```

**Quick-Fix routing** (use `--quick <id>`):
- `effort` is `micro` or `small` AND `type` is `bug`, `chore`, or `task`
- No external API changes (no new integrations in the bead description)

**Full orchestrator** (default, no flag needed):
- `type` is `feature`
- `effort` is `medium`, `large`, `xl`, or empty
- Bead involves external API integrations

### Dispatch Command

Build the dispatch command from the Wave Table classifications. Full-mode beads are
positional args, quick-mode beads use `--quick <id>`:

```bash
# Mixed wave: some full, some quick-fix (from Wave Table modes)
./scripts/wave-dispatch.sh mira-adapters-0al --quick mira-fix-x3r --quick mira-adapters-doq > /tmp/wave-config.json
```

Or with an explicit workspace:
```bash
./scripts/wave-dispatch.sh mira-adapters-0al --quick mira-fix-x3r --workspace workspace:5 > /tmp/wave-config.json
```

The script:
1. Creates horizontal splits (`cmux new-split right`) with 3s delays between them
2. Renames each surface tab to `<short-id>-impl` (full) or `<short-id>-qf` (quick-fix)
3. Dispatches `cld -b <bead-id>` (full) or `cld -bq <bead-id>` (quick-fix) to each surface
4. Outputs a wave config JSON to stdout (save this — it's the input for monitoring)

**Output format** (saved to `/tmp/wave-config.json`):
```json
{
  "dispatch_time": "2026-03-30T14:00:00",
  "workspace": "workspace:5",
  "wave_id": "wave-20260330-140000",
  "beads": [
    {"id": "mira-adapters-0al", "surface": "surface:3", "mode": "full"},
    {"id": "mira-fix1", "surface": "surface:5", "mode": "quick"}
  ]
}
```

After dispatch, confirm to the user which beads were dispatched to which surfaces and in which mode.

**Important**: The dispatch script uses `cld -b` (full) or `cld -bq` (quick-fix) based
on the `--quick` flag. Both modes run single-pane — no separate review surface.

---

## Phase 5: Monitoring (delegated to wave-monitor)

Monitoring is delegated to the wave-monitor Haiku subagent. Spawn it ONCE per wave
and block until it returns a terminal verdict. This parks the orchestrator's context
during the monitoring window — cost-efficient for multi-hour waves.

**Cost model:** Haiku at <$0.001/call vs Opus at $0.06+/call for the same check.
1 Haiku invocation total — bash sleep loops don't re-read context, so cost is fixed
regardless of poll count. Polling every 60s on a 4-hour wave = 240 polls, all free.

### Invoking wave-monitor

```python
monitor_result = Agent(
    subagent_type="beads-workflow:wave-monitor",
    prompt=json.dumps({
        "wave_config_path": "/tmp/wave-config.json",
        "stuck_threshold_hours": 4,
        "review_loop_max_iterations": 3,
        "poll_interval_seconds": 60
    })
)
verdict = json.loads(monitor_result)
# verdict.status: complete | needs_intervention
```

The `wave_config_path` is the JSON file output by `wave-dispatch.sh` (saved to
`/tmp/wave-<wave_id>.json` or the path you provided to wave-dispatch.sh output redirect).

The parent orchestrator parks (context NOT re-read) until wave-monitor returns.
wave-monitor uses `bash sleep 60` between polls — not ScheduleWakeup — so the
blocking Agent() call stays open for the full monitoring window. (60s is safe because
bash sleep keeps the agent alive; no context re-read between polls unlike ScheduleWakeup.)

### Branching on wave-monitor verdict

Parse the verdict JSON and branch on `status` and `reason`:

---

#### verdict: complete

All beads closed, all panes idle. wave-monitor confirms the wave is done.

```json
{"status": "complete", "summary": {"bead_count": 4, "elapsed_minutes": 87, "polls_run": 20}}
```

**Action:** Proceed to Phase 6 (wave completion and transition).

---

#### verdict: needs_intervention — reason: pane-error

One or more panes show error/crash signals (ECONNREFUSED, fatal, panic, traceback).

```json
{
  "status": "needs_intervention",
  "reason": "pane-error",
  "bead_id": "<id>",
  "details": "Pane surface:3 shows: ECONNREFUSED at tail-5"
}
```

**Action:**
1. Read the surface manually:
   ```bash
   cmux read-screen --surface <surface> --lines 30
   ```
2. **If recoverable** (transient ECONNREFUSED, test setup failure):
   - Re-dispatch the bead to a new surface:
     ```bash
     ./scripts/wave-dispatch.sh <bead-id> > /tmp/wave-config-updated.json
     ```
   - Update the wave config path and re-spawn wave-monitor with the updated config
3. **If not recoverable** (fatal crash, missing dependency, bead in a broken state):
   - Escalate to user with the full `details` string and surface scrollback
   - Leave the bead `in_progress`
   - Continue monitoring remaining beads by re-spawning wave-monitor with a config
     that excludes the problematic bead

---

#### verdict: needs_intervention — reason: stuck

A bead has been `in_progress` longer than `stuck_threshold_hours` with no surface
activity and no recent agent_calls in metrics.db.

```json
{
  "status": "needs_intervention",
  "reason": "stuck",
  "bead_id": "<id>",
  "details": "Bead in_progress for 5.2h (threshold: 4h). Surface idle. No recent agent_calls."
}
```

**Action:**
1. Read the surface to assess actual state:
   ```bash
   cmux read-screen --surface <surface> --scrollback --lines 50
   ```
2. Check bead notes for orchestrator context:
   ```bash
   bd show <bead_id>
   ```
3. **False-positive guard:** Verify this is not a long-running Codex adversarial run.
   A bead is truly stuck only after **two consecutive identical checks** where the screen
   output hasn't changed AND processes show no CPU usage. A single unchanged check is
   normal during long integration tests or sleep recovery.
4. If genuinely stuck — escalate to user. The user decides:
   - Kill-and-redispatch: `cmux kill-pane <surface>` then re-dispatch
   - Skip the bead (leave in_progress, exclude from this wave)
   - Leave and wait (if user believes it will recover)
5. If the user chooses to continue without the stuck bead: re-spawn wave-monitor with
   a config that excludes the stuck bead's surface from the `complete` check.

---

#### verdict: needs_intervention — reason: review-loop

A pane has hit `review_loop_max_iterations` Codex review iterations (default: 3).

```json
{
  "status": "needs_intervention",
  "reason": "review-loop",
  "bead_id": "<id>",
  "details": "Detected 3 review iterations in pane scrollback (threshold: 3)."
}
```

**Action:**
1. Read the surface scrollback to see actual review content:
   ```bash
   cmux read-screen --surface <surface> --scrollback --lines 200
   ```
2. **Do NOT intervene automatically** — present the situation to the user:
   ```
   ## Review Loop Detected: <bead_id>

   Review iteration count has reached the threshold (3). The bead may be oscillating
   in a fix-review cycle. Scrollback summary: <key findings from scrollback>

   Options:
   A) Continue monitoring (re-spawn wave-monitor with higher review_loop_max_iterations=5)
   B) Skip review risk — proceed without further review iterations (logged to bead notes)
   C) Abort the bead (leave in_progress, surface stays active)
   ```
3. If user chooses A: re-spawn wave-monitor with `review_loop_max_iterations` increased
4. If user chooses B: log to bead notes and continue monitoring
5. If user chooses C: escalate the bead to the stall list and continue with remaining beads

---

#### verdict: needs_intervention — reason: ambiguous

`wave-completion.sh` itself errored (exit code 2) or returned non-JSON, or the wave
config file was not found.

```json
{
  "status": "needs_intervention",
  "reason": "ambiguous",
  "bead_id": null,
  "details": "wave-completion.sh exited with code 2. stderr: <captured>"
}
```

**Action:**
1. Check wave config file still exists:
   ```bash
   cat /tmp/wave-config.json
   ```
2. If config is missing: something cleaned up `/tmp` prematurely. Reconstruct from
   wave-dispatch.sh output if you have it saved elsewhere, or ask the user to re-dispatch.
3. If config is present but completion script failing:
   - Attempt one manual run:
     ```bash
     ./scripts/wave-completion.sh /tmp/wave-config.json
     ```
   - Read the script output/error and diagnose
4. If infrastructure issue persists: escalate to user with full `details` from verdict.
   **Do NOT loop indefinitely** — if the script is broken, the orchestrator cannot
   monitor autonomously. Leave beads in their current state and report.

---

### Re-spawning wave-monitor after intervention

After handling an intervention case, re-spawn wave-monitor if monitoring should continue:

```python
# Re-spawn with same or adjusted parameters
monitor_result = Agent(
    subagent_type="beads-workflow:wave-monitor",
    prompt=json.dumps({
        "wave_config_path": "/tmp/wave-config.json",  # may be updated
        "stuck_threshold_hours": 4,
        "review_loop_max_iterations": 5,  # may be adjusted
        "poll_interval_seconds": 60
    })
)
```

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
  "unclosed_follow_ups": [{"id": "mira-fix-x3r", "status": "open"}],
  "stalls": [{"id": "mira-0al", "detected_at": "2026-04-20T14:32:00Z", "elapsed_minutes": 17}]
}
```

Use this for quick polling between full status checks. The exit code makes it easy to
use in a loop or conditional.

### Session Close — FORBIDDEN for the Wave Orchestrator

**The wave orchestrator must NEVER trigger `session close` or send `cmux send "session close"`.**

The bead-orchestrator handles the full lifecycle autonomously (single-pane mode):
1. Implementation → Codex adversarial review (inline, no separate pane)
2. Opus fix loop (up to 2 iterations) → verification gate → session close
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

### Pipeline Check After Session Close

When wave-monitor returns `complete` (all beads closed, all surfaces idle), check whether
the CI pipeline for the pushed commits passed **before** treating the wave as fully done:

```bash
# Find the most recent run on main (session-close merges feature→main)
gh run list --branch main --limit 3 --json databaseId,status,conclusion,headSha,createdAt \
  | jq 'map(select(.status == "completed")) | .[0]'
```

**If conclusion is `success`**: wave is truly done, proceed.

**If conclusion is `failure` or `cancelled`**: spawn a fix agent:

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

**Timing note**: Wait up to 2 minutes for the pipeline run to appear after wave-monitor
returns complete. If no run appears, check whether the repo has CI configured
(`ls .github/workflows/`). If no CI config exists, treat the wave as done.

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

## Phase 6.5: Integration-Verification (Final Wave Gate)

After all beads in an epic are closed and CI passes, run a cross-bead invariant check
before declaring the epic complete. This catches gaps that individual bead reviews cannot
see — specifically: missing scopes, broken cross-bead contracts, and data-model
inconsistencies that only surface when all implementations are combined.

**This is a gate on epic completion, not on individual bead session-close — CRITICAL findings prevent the epic from being declared complete and trigger a remediation wave.** Integration-Verification runs AFTER all beads have already closed, triggered by the wave-orchestrator.

**When to run:**
- wave-monitor returned `complete` AND `wave-completion.sh` returns exit code 0 (all beads closed, all surfaces idle)
- All CI pipelines for the wave have passed (see Pipeline Check above)
- This is the **final wave** of the epic — either the user explicitly confirms ("no more waves") or the wave plan from Phase 1 shows all beads are now closed
- `--skip-integration-check` flag is NOT set

**Skip conditions:**
- `--skip-integration-check` flag set → log skip, proceed to Phase 7
- Single-bead **epic** (no cross-bead invariants possible)

> **Note**: The absence of `.beads/integration-check.sh` is NOT a skip condition — it triggers the fallback agent instead (see "Spawning the Verification Agent" below). `SKIPPED` status is reserved exclusively for the two conditions above.

### Running the Integration Check

Check for a project-specific integration check script:

```bash
# Non-zero exit is expected when FAIL. Always read JSON status for dispatch.
if [[ -f .beads/integration-check.sh ]]; then
  bash .beads/integration-check.sh > /tmp/integration-check-results.json || true
fi
# Script absent → fall through to agent fallback below
```

If the script is absent (or the if-block above did not execute), proceed to the "Spawning the Verification Agent" section below.

The script must output JSON with this structure:
```json
{
  "status": "PASS | FAIL | SKIPPED | ERROR",
  "findings": [
    {
      "severity": "CRITICAL | WARNING | INFO",
      "category": "missing_scope | broken_contract | data_inconsistency | other",
      "description": "What the check found",
      "recommendation": "What to do about it"
    }
  ],
  "environment": "production | staging | local",
  "checked_at": "ISO-8601 timestamp"
}
```

### Spawning the Verification Agent

If `.beads/integration-check.sh` does NOT exist, spawn a general-purpose subagent to
attempt automated discovery of cross-bead invariants from the codebase:

```
Agent(subagent_type="general-purpose", prompt="
  ## Cross-Bead Integration Verification

  All beads in this wave are now closed. Perform a cross-bead invariant check to
  catch gaps that individual bead reviews cannot see.

  ## Wave Summary
  Beads completed: <list from wave-config.json>

  ## What to check (in priority order)
  1. Shared scopes / categories: Are there external authority catalogs (medical codes,
     legal registries, financial identifiers) that should have a universal scope
     (no adapter-prefix) but were implemented with per-adapter scopes instead?
  2. Cross-bead contracts: Do any two beads share an interface? If so, are both sides
     consistent (field names, types, optional/required)?
  3. Data consistency: Are there any entities that are written by one bead and read by
     another? Check that the schema is consistent.
  4. Missing types/categories: Compare the expected value set (from domain knowledge
     or CLAUDE.md) against what was actually implemented. Are any values missing?

  ## Output
  Return JSON matching the integration-check.sh schema above.
  Status PASS if no CRITICAL findings. FAIL if one or more CRITICAL findings.
")
```

### Processing Results

| Status | Action |
|--------|--------|
| `PASS` | Log results to bead notes, proceed to Phase 7 |
| `FAIL` | Create follow-up beads for each CRITICAL finding. Do NOT proceed to Phase 7. Schedule a remediation wave for the follow-up beads. The epic is not complete until the remediation wave has been run and Phase 6.5 returns PASS or SKIPPED. Exception: `--skip-integration-check` bypasses this gate. |
| `SKIPPED` | `--skip-integration-check` flag was set, or single-bead epic. Log advisory and proceed to Phase 7. |
| `ERROR` | Infrastructure issue — do NOT create follow-up beads. Alert operator. Re-run manually once infrastructure is restored. Do NOT advance to Phase 7. |

**Creating follow-up beads from CRITICAL findings:**
```bash
# For each CRITICAL finding from integration check results:
bd create \
  --title="[INTEGRATION] Fix <finding category>: <short description>" \
  --type=task \
  --priority=1 \
  --description="Found during integration-verification of wave N.

Finding: <description>
Recommendation: <recommendation>

Discovered by integration-verification after epic close."
```

Log the created beads to the wave's bead notes and include them in the Phase 7 Learnings Report.

### Reference

See `references/integration-verification-guide.md` for:
- Domain-specific canonical-catalog taxonomy
- Example `.beads/integration-check.sh` for live environment queries (Aidbox, Postgres, etc.)
- Regression scenario: How the KBV/DIMDI universal-category gap would have been caught

---

## Phase 7: Learnings Report

After each wave completes (all beads closed, all surfaces idle), generate a structured
learnings report BEFORE surfaces are cleaned up. The reviewer scrollback is the primary
data source and is lost once surfaces close.

### Data Collection (per bead)

For each completed bead, collect:

1. **Bead notes**: `bd show <id>` — close reason, iteration count, quality grade
2. **Reviewer findings**: Extracted from the bead's own surface scrollback (single-pane
   inline review — no separate reviewer surface):
   ```bash
   cmux read-screen --surface <bead-surface> --scrollback --lines 500
   ```
   Look for BLOCKING findings (fixed), ADVISORY findings (deferred), Codex REGRESSION markers
3. **Implementation commits**: `git log --oneline <branch>` — what actually changed
4. **Follow-up beads created**: beads with `discovered-from: <bead-id>` in the wave
5. **Auto-decisions**: scan `bd show <id>` bead notes for entries matching the
   `DECISION: auto-` pattern. Parse: phase name, decision taken, reviewer
   recommendation (if present), grade impact (if present). Note that
   `bead_runs.auto_decisions` and `bead_runs.deviations_from_reco` provide aggregate
   counts if the orchestrator populated them — the bead notes scan is the richer
   source for per-decision detail.

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

### Auto-Decisions Made (require post-hoc review)
[Omit this section if no auto-decisions were made in this wave]

| Bead | Phase | Decision | Reviewer Recommendation | Grade Impact |
|------|-------|----------|------------------------|--------------|
| <id> | <phase> | auto-accept | <recommendation if present> | <e.g. A→B> |

### Token Usage (wave <wave_id>)
| Mode | Beads | Total Tokens | Avg/Bead | Codex Tokens | Claude Tokens |
|------|-------|--------------|----------|--------------|---------------|
| full-1pane | 3 | ... | ... | ... | ... |
| quick | 2 | ... | ... | ... | ... |

| Model | Calls | Total Tokens |
|-------|-------|--------------|
| claude-opus-4-7 | 12 | ... |
| claude-sonnet-4-6 | 8 | ... |
| gpt-5-codex | 9 | ... |

### CLAUDE.md Updates Made
[List any project CLAUDE.md changes made during this wave]
```

### Data Sources (Token Breakdown)

Use these SQL queries against the beads database to populate the Token Usage tables.
Replace `<wave_id>` with the current wave identifier.

**Per-mode breakdown** (maps to the Mode table):

```sql
SELECT
  br.mode,
  COUNT(DISTINCT br.bead_id)          AS beads,
  SUM(br.total_tokens)                AS total_tokens,
  SUM(br.total_tokens) / COUNT(DISTINCT br.bead_id) AS avg_per_bead,
  SUM(br.codex_total_tokens)          AS codex_tokens,
  SUM(br.total_tokens) - SUM(br.codex_total_tokens) AS claude_tokens
FROM bead_runs br
WHERE br.wave_id = '<wave_id>'
GROUP BY br.mode
ORDER BY beads DESC;
```

**Per-model breakdown** (maps to the Model table):

```sql
SELECT
  ac.model,
  COUNT(*)               AS calls,
  SUM(ac.total_tokens)   AS total_tokens
FROM agent_calls ac
WHERE ac.wave_id = '<wave_id>'
GROUP BY ac.model
ORDER BY total_tokens DESC;
```

**DB Schema reference:**
- `bead_runs`: `bead_id`, `wave_id`, `mode` (e.g. `full-1pane`, `quick-fix`),
  `total_tokens`, `codex_total_tokens`, `auto_decisions`, `deviations_from_reco`
- `agent_calls`: `run_id`, `bead_id`, `wave_id`, `phase_label`, `agent_label`,
  `model`, `total_tokens`, `duration_ms`

For mixed waves (quick + full beads), both tables will have rows for each mode used.
Omit the Token Usage section only if `bead_runs` contains no rows for the wave.

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

Generate the report AFTER wave-monitor returns `complete` and `wave-completion.sh` returns
exit 0, but BEFORE starting the next wave. The reviewer scrollback must still be accessible
— if surfaces have already been cleaned up, fall back to bead notes and git log (less rich
but still useful).

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

- **Output language**: Respond in the user's language. The agent instructions are English but output should match the user.
- **Use the scripts**: Prefer `wave-dispatch.sh`, `wave-status.sh`, and `wave-completion.sh` over manual cmux calls. They're faster, produce structured output, and reduce context usage.
- **NEVER session close**: The wave orchestrator must never trigger or send `session close`. The bead-orchestrator (or quick-fix) handles this autonomously.
- **`--skip-wave-review` skips Phase 1.25**: Always log the skip per bead with timestamp and `$(whoami)`.
- **`--dry-run` runs Phase 1.25 read-only**: Findings are shown but NO bd update edits are applied.
- **Phase 1.25 max 1 re-review**: Never loop more than once. After second-pass still-not-ready, escalate to user with Continue/Abort.
- **NEVER reuse surfaces**: Always dispatch to fresh surfaces via `wave-dispatch.sh`.
- **Integration-verification after epic**: After the final wave closes, always run Phase 6.5 to catch cross-bead gaps. Skip only with `--skip-integration-check` and only when there are no cross-bead invariants to check (e.g. single-bead waves).
- **Delegate scenarios**: Delegate scenario generation to subagents, not inline.
- **Check conflict risk upfront**: Before wave dispatch, check if beads will modify the same files. If so: max 2 parallel or use sub-waves.
- **Stuck = 2x identical**: A bead is only "stuck" after two consecutive identical status checks with no CPU usage. A single unchanged check is normal.
- **No time estimates**: Don't predict how long individual beads will take.
- **User confirms waves**: Never auto-dispatch without user approval.
- **Scenarios before dispatch**: Feature beads without scenarios waste pane time.
- **max 4-5 panes**: Beyond 5, layout overhead and resource contention become issues.
- **Pull between waves**: Always `git pull --no-rebase` + `bd dolt pull` between waves.
- **Monitoring is delegated**: Poll monitoring is handled by wave-monitor (Haiku subagent). The orchestrator parks during monitoring — no direct ScheduleWakeup in the orchestrator.
- **Don't intervene in bead surfaces**: Bead-orchestrators run single-pane (inline Codex review, no separate reviewer surface). Only intervene when the bead surface appears dead and bd status is still in_progress (stall scenario — see stall detection in wave-monitor).
