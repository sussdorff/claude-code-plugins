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
| `--skip-review` | Skip architecture review (Phase 1.5b) for all beads. Logged to audit. |
| `--skip-integration-check` | Skip Phase 6.5 integration-verification (cross-bead invariant check after final wave) |

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

**Pane budget:** All beads use 1 pane each. After CCP-2vo.4, full beads run their Codex
review inline (no separate review pane, no `cld -br`). Quick-fix beads were already 1-pane.
Factor this into `max-parallel` calculations: a wave of 2 full + 2 quick needs 4 panes.

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

## Phase 1.5b: Architecture Review (Design-Doc Gate)

After scope analysis (Phase 1.5), assess each bead for architectural complexity. Beads
that involve design decisions (boundaries, state machines, API contracts) get a structured
architecture review BEFORE implementation — preventing costly review oscillation.

**Skip this phase if `--skip-review` is set.** Log the skip:
```bash
bd update <id> --append-notes="⚠ Architecture review skipped (--skip-review flag). User: $(whoami), $(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

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
    "Fehlender Universal-Scope fuer <Katalog-Name>: Kanonische Referenzdaten benoetigen
     einen eigenstaendigen Scope ohne adapter-prefix, damit alle Adapter denselben
     Referenz-Datensatz nutzen."

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
   bd update <id> --append-notes="⚠ Architecture Council BLOCKED but user overrode. Findings: <summary>. $(date -u +%Y-%m-%dT%H:%M:%SZ)"
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

**Important**: Do NOT use `cld -br` — that's for review-only sessions. The dispatch script
uses `cld -b` (full) or `cld -bq` (quick-fix) based on the `--quick` flag.

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
| `dead` | Pane closed (cmux returns "not a terminal") | Normal if bead closed, abnormal if bead still in_progress (orphan worktree) |
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

Bead-orchestrators typically run 10–30 min. To keep the wave orchestrator's own
prompt cache warm across a wave, **every poll interval must stay under 270s** (the
Anthropic prompt cache TTL is 5 minutes — any gap ≥300s forces a full-context
re-read on the next wake).

| Poll | Delay from previous | Elapsed | Purpose |
|------|---------------------|---------|---------|
| #1 | 270s | T+4.5 min | Catch immediate failures (missing scenario, crash-on-start) |
| #2 | 270s | T+9 min | Early progress signal |
| #3 | 270s | T+13.5 min | Mid-point — quick-fix beads may already be done |
| #4+ | 270s | every 4.5 min | Continue until `wave-completion.sh` returns 0 |

**Why not 1500s (25 min) polls?** Fewer polls but each one eats a full cache miss,
and you miss fast quick-fix completions. 270s gives 13 cache-warm polls per hour
vs. 2–3 cache-miss polls — strictly better for a 10–30 min workload.

**Why not <270s?** Sub-270s adds poll cost without buying anything — bead state
rarely changes meaningfully in under 4 minutes, and the cache window is the same.

**Implementation — use `ScheduleWakeup`** between checks, not `run_in_background`
sleeps. `ScheduleWakeup(delaySeconds=270, prompt="/wave-orchestrator monitor", ...)`
lets the runtime clamp correctly and surfaces the poll cadence to the user. The
runtime clamps to [60, 3600], so 270 is honored as-is.

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

### Stall Detection

A bead is **stalled** when:
- Its surface is idle (shows a bare shell prompt)
- `bd show <id>` reports `in_progress` (bead not closed)
- Elapsed time since dispatch exceeds **15 minutes**

When `wave-completion.sh` detects a stall, it:
1. Logs a clear alert in the JSON output: `stalls` array with bead ID and timestamp
2. Writes a diagnostic note to the bead:
   `STALL-DETECTED: wave-orchestrator observed surface idle + bd in_progress at <timestamp>. Manual investigation required.`
3. **Does NOT trigger session-close or spawn fix agents**
4. **Continues monitoring** remaining beads

The wave orchestrator then surfaces the stall to the user in the status table and the Phase 7 Learnings Report.

**False-positive guard:** Long Codex adversarial runs (Opus reasoning, 15+ min) can sit
silent mid-execution. Before emitting a stall, `wave-completion.sh` applies a guard:
1. Query `agent_calls` for recent activity: `agent_calls` is read from `~/.claude/metrics.db`
   via `sqlite3` (not via `bd sql` — this table is a SQLite file, not in the Dolt beads DB).
   The query compares epoch seconds (`strftime('%s','now') - strftime('%s', recorded_at)`) to
   avoid text-sort mismatch between ISO-8601+TZ stored values and SQLite's `datetime()` output.
   If any row for this bead was recorded within the last 5 minutes → **NOT stalled, skip alert**.
2. Scrollback fallback (if `agent_calls` query fails or returns 0): check the surface
   scrollback for tool-use markers (Bash, Read, Write, Edit, Grep, etc.) in the last 30
   lines. If present, the run recently executed tools → **NOT stalled, skip alert**.

**Idempotency:** The bead note is written **at most once per wave run** via a temp-file
marker (`/tmp/wave-stall-<wave_id>-<bead_id>`). The STALL entry is still added to the
`stalls` JSON array on every subsequent poll (useful for monitoring dashboards), but the
bead tracker is not spammed on every 270s check.

The mock scenario used in acceptance: a bead with surface-idle + bd in_progress + elapsed
> 15 min produces a STALL alert. A second bead with surface-idle + bd in_progress but
recent tool-use markers in scrollback does NOT trigger a stall alert.

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
- `wave-completion.sh` returns exit code 0 (all beads closed, all surfaces idle)
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
2. **Reviewer findings** (if cmux-reviewer was used):
   ```bash
   # Read reviewer surface scrollback before it's cleaned up
   cmux read-screen --surface <reviewer-surface> --scrollback --lines 100
   ```
   Extract: BLOCKING findings (fixed), ADVISORY findings (deferred), Codex findings
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
- **Integration-verification after epic**: After the final wave closes, always run Phase 6.5 to catch cross-bead gaps. Skip only with `--skip-integration-check` and only when there are no cross-bead invariants to check (e.g. single-bead waves).
- **Delegate scenarios**: Delegate scenario generation to subagents, not inline.
- **Check conflict risk upfront**: Before wave dispatch, check if beads will modify the same files. If so: max 2 parallel or use sub-waves.
- **Stuck = 2x identical**: A bead is only "stuck" after two consecutive identical status checks with no CPU usage. A single unchanged check is normal.
- **No time estimates**: Don't predict how long individual beads will take.
- **User confirms waves**: Never auto-dispatch without user approval.
- **Scenarios before dispatch**: Feature beads without scenarios waste pane time.
- **max 4-5 panes**: Beyond 5, layout overhead and resource contention become issues.
- **Pull between waves**: Always `git pull --no-rebase` + `bd dolt pull` between waves.
- **Stay cache-warm**: Poll every 270s (not 300s+, not <60s). First check at T+4.5min. 270s keeps the prompt cache alive across the full wave; gaps ≥300s force a full-context re-read.
- **Don't intervene in bead surfaces**: Bead-orchestrators run single-pane (no `cld -br`, no separate reviewer). Only intervene when the bead surface appears dead and bd status is still in_progress (stall scenario — see stall detection).
