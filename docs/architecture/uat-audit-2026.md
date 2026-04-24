# UAT Audit & Fixture Strategy — 2026

## Audit: Current Reality

### Projects Surveyed

All 44 bead-tracked projects (identified by presence of `.beads/` directory) were checked for
`uat-config.yml`. Results:

| Finding | Count | Notes |
|---------|-------|-------|
| Projects with `uat-config.yml` | **1** | MIRA only (`~/code/mira/.claude/uat-config.yml`) |
| Projects without `uat-config.yml` | 43 | All use the bead-orchestrator but have no UAT config |
| Projects with Playwright / e2e test infrastructure | ~3 | MIRA, erp-project-open (Cypress), polaris |
| Projects with fixture directories | ~5 | claude-code-plugins, claude-nexus, open-brain, polaris, mcp/mcp-ddce |

### What Happens in Phase 13 Without `uat-config.yml`

The bead-orchestrator Phase 13 explicitly skips UAT when either:
1. Routing was GSD mode (type=task/chore/bug with micro/small effort)
2. `uat-config.yml` does not exist in the project

For the 43 projects without `uat-config.yml`, **Phase 13 is a silent no-op for PAUL-mode
beads** — a feature bead on any of those projects (type=feature or effort=medium/large)
will trigger PAUL-mode routing, reach Phase 13, and immediately skip it. There is no
warning, no fallback, no logged indication that UAT was intended but could not run.

This is a silent quality gap: the pipeline claims PAUL-mode thoroughness but delivers
GSD-mode UAT coverage.

### PAUL-Mode Routing Analysis

PAUL mode triggers when ANY of the following are true:
- `type: feature` (regardless of effort)
- `effort: medium` or `effort: large`
- MoC type includes `e2e`, `demo`, or `integ`

Of the 43 projects without UAT config, any feature beads on those projects will silently
skip UAT. Projects with active feature development that lack UAT config include:
`cognovis-library`, `cognovis-website`, `zahnrad`, `polaris`, `MCN_ZulassungsCockpit`,
`fhir-praxis-de`, `fhir-dental-de`, and many cli-tools projects.

### What MIRA's UAT Config Actually Tests

MIRA is the only project with a `uat-config.yml`. Analysis of its content:

**Configured `playwright_scenarios` (static, generic):**
- `dashboard-loads`: Navigates to dashboard, logs in, checks for visible data widget
- `core-feature-flow`: "Navigate to main feature area, perform representative action, verify result persisted"

The `core-feature-flow` scenario is deliberately vague — it does not name any MIRA-specific
feature, form, or data element. It cannot be automated as written; it requires a human or
bead-specific context to execute meaningfully. This means the `playwright_scenarios` in
MIRA's `uat-config.yml` are effectively documentation placeholders, not executable tests.

**What actually runs during UAT for MIRA beads:**
Per `uat-validator.md` Step 7, the validator is instructed to "derive UAT scenarios from
`bead_description`" — not from `playwright_scenarios`. The static scenarios in
`uat-config.yml` are run as-is, but the validator's primary work is scenario derivation
from acceptance criteria. The generic `core-feature-flow` adds noise without signal.

**Existing Playwright infrastructure in MIRA (`e2e/`):**
MIRA has a real Playwright test suite at `mira/e2e/` with 8+ spec files including
`smoke-check.spec.ts`, `karteikarte-pvs.spec.ts`, `billing-optimization.spec.ts`, etc.
These are bead-authored tests checked into the repo. They use seed data (seeded via
`bun run dev:all`) and hardcoded dates (e.g. `2026-03-03`). None of these are connected
to the `uat-config.yml` `playwright_scenarios` section — they are standalone Playwright
tests run via `bun playwright test`, not via the UAT validator.

**Gap**: The uat-config.yml and the actual e2e/ test suite are disconnected. UAT could
run `bun playwright test e2e/smoke-check.spec.ts` as a smoke test, but this is not
configured.

### Fixture Inventory

| Project | Fixture type | Location | Nature |
|---------|-------------|----------|--------|
| claude-code-plugins | Scenario/design fixtures | `tests/fixtures/bead-orchestrator-fixtures.md` | Markdown scenario descriptions for orchestrator branch testing; NOT executable test fixtures |
| claude-code-plugins | Test data | `tests/fixtures/vision/`, `tests/fixtures/vision-review/` | JSON/data files for vision agent tests |
| claude-nexus | Test transcripts | `tests/fixtures/` | `.jsonl` transcripts for agent testing |
| open-brain | Python test data | `python/tests/fixtures/` | Static data for unit tests |
| polaris | Package fixtures | `packages/pvs-x-isynet/fixtures/` | Unknown — likely static data |
| mcp/mcp-ddce | Test fixtures | `test/fixtures/` | Unknown |

**Finding**: No project has UAT-specific fixtures (i.e. pre-generated application state
or API response fixtures designed for UAT execution). All fixture directories found
serve unit/integration tests, not UAT.

### UAT Silent-Fail Conditions

The `uat-validator.md` pre-flight checklist will report `BLOCKED` (not silent-fail) when:
- `uat_config_path` does not exist or is not readable
- `bead_description` is empty or unreadable
- Setup commands fail (e.g. `bun install` exits non-zero)
- For web projects: `portless_namespace` is missing from the orchestrator prompt
- The dev server does not respond within the wait loop

However, in the orchestrator (Phase 13), the skip condition `uat-config.yml does not exist`
means BLOCKED is never reached for the 43 no-config projects — UAT is skipped entirely
before spawning the validator, so the validator never reports BLOCKED. The orchestrator
proceeds silently.

**One genuine silent-fail vector**: If the orchestrator does not pass `portless_namespace`
to the UAT context block for a web project, the validator will reach BLOCKED. Given that
`cld -b <id>` derives the namespace from `bd config get issue_prefix + bead number`, and
this derivation may fail for non-MIRA projects, portless namespace propagation is a latent
reliability issue.

---

## Problem Statement

1. **UAT is effectively disabled on 43 of 44 bead-tracked projects.** No `uat-config.yml`
   means Phase 13 silently no-ops. Feature beads on these projects claim PAUL-mode
   quality gates but receive no user-acceptance verification.

2. **MIRA's UAT scenarios are generic and not bead-aware.** The `playwright_scenarios`
   in MIRA's `uat-config.yml` describe vague steps that cannot be mechanically derived
   into executable tests. The validator must improvise from bead acceptance criteria,
   which is the intended behavior — but the static scenarios provide no value and may
   create confusion about what is "being tested."

3. **No project has fixture-based UAT.** All existing fixture directories serve unit
   tests. UAT relies on live application state (MIRA) or implicitly on nothing (everyone else).

4. **The uat-validator and the MIRA e2e/ test suite are not connected.** MIRA has real,
   working Playwright tests that cover smoke and feature scenarios. These are not
   referenced from `uat-config.yml` at all.

5. **mira-adapters does not exist yet** but is a planned cross-repo scenario. No
   coordination mechanism exists for sharing fixtures between repos.

---

## Strategy Options

### Option A: Fixtures-Only

Pre-generate application state (API responses, database snapshots, seeded datasets) and
check them into the repo. UAT runs against these fixtures using a mock server or
replay mechanism rather than a live application.

**Pros:**
- Deterministic: same input every run, no flakiness from server state
- Fast: no server startup time
- Works offline, no infrastructure requirements
- Easy to version and diff alongside code changes

**Cons:**
- **Drift risk**: Fixtures go stale as schemas and API responses evolve. Must be
  regenerated after schema changes or the tests pass against an outdated contract.
- Generation mechanism needed: who creates the fixtures? Automated seeding script or
  manual snapshot?
- Cannot test rendering, browser behavior, or UI flows — only API contracts
- Fixtures for complex stateful UIs (e.g. MIRA's billing flow) are large and brittle

**Drift risk rating**: HIGH for data-heavy applications with evolving schemas (MIRA).
LOW for stable CLI tools or library APIs.

**Best fit**: Library projects, CLI tools, and stable API contracts where the schema
changes infrequently.

---

### Option B: Live-App (current MIRA approach)

Start the actual dev server with seeded data and run tests against the running application.
This is what MIRA's `uat-config.yml` describes: `bun run dev:all`, wait for health check,
run Playwright.

**Pros:**
- Tests real behavior end-to-end — rendering, routing, data flows
- No fixture drift: the app is always tested against its own live state
- Can be augmented with bead-specific seed data
- MIRA already has this infrastructure (Playwright, AppBox, Portless)

**Cons:**
- **Infrastructure cost**: requires a running Bun + database server per UAT invocation.
  On a CI-less, developer-machine setup this means the dev server must be startable
  and the database must be seeded before each UAT run.
- Flakiness: network timing, port availability, seed data variance
- Slow: server startup + health polling adds 30-120 seconds per UAT session
- Cross-machine portability issues: hardcoded credentials (1Password: mira-test-user),
  hardcoded namespaces, hardcoded dates in existing e2e tests
- Cannot run in parallel across multiple bead worktrees sharing the same Portless namespace

**Drift risk rating**: LOW — the app tests itself. But test code (e2e specs) can become
stale if bead-specific scenarios are never cleaned up.

**Best fit**: Web applications with stable infrastructure, clear seeding mechanisms,
and test suites that evolve with the app.

---

### Option C: Hybrid

Use fixtures for unit-level UAT (API contract tests, CLI output validation) and live-app
for integration/browser UAT when the project warrants it.

**Structure:**
- `uat_strategy.mode: smoke` → runs CLI or `curl` smoke tests against fixtures or a
  minimal API server (no browser)
- `uat_strategy.mode: playwright` → starts full dev server and runs browser scenarios
- `uat_strategy.mode: import_check` → verifies library exports and types (zero infra)

The orchestrator already models these three modes. The hybrid approach simply assigns
the appropriate mode per project type rather than defaulting to a single strategy.

**When to use which mode:**

| Project type | Recommended mode | Rationale |
|-------------|-----------------|-----------|
| CLI tool | `smoke` | Binary installed, run commands, check exit codes + output |
| Python/JS library | `import_check` | Import the module, check exported symbols |
| REST API only | `smoke` (curl) | Health check + key endpoint smoke tests |
| Web app (full-stack) | `playwright` | Browser rendering + user flows require live app |
| Web app (API-heavy) | `smoke` + optional `playwright` | API tests with selective browser verification |

**Cross-cutting recommendation**: All projects should define `smoke_tests` in `uat-config.yml`
at minimum — even a single `which <binary>` or `curl health` check is better than no UAT
at all.

---

## Cross-Repo Fixture Coordination

### Problem

When `mira-adapters` (a planned future project containing adapter/integration logic for
MIRA) needs to run UAT, it may require:
1. MIRA API responses as fixture data (to test adapters against realistic payloads)
2. A running MIRA instance (for integration UAT)
3. Database seed data that MIRA manages

These artifacts are owned by the MIRA repo but consumed by the mira-adapters UAT.

### Design: MIRA ↔ mira-adapters

**Option 1: Published Fixtures Artifact**

MIRA runs a fixture-generation step (e.g. `bun run generate:fixtures`) that dumps
API response snapshots to a known path. These are published as a versioned artifact
(tarball, npm package, or Git submodule) consumed by mira-adapters' test setup.

```
mira/scripts/generate-uat-fixtures.sh
  → dist/uat-fixtures/
    → api-proposals-response.json
    → api-staff-auth-response.json
    → ...
```

mira-adapters `uat-config.yml`:
```yaml
setup:
  install: ["bun install", "curl -L <mira-fixtures-url> | tar -xz -C tests/fixtures/"]
```

Pros: decoupled, versioned, no live MIRA needed.
Cons: requires a fixture generation + publishing pipeline; drift risk.

**Option 2: Bead Dependency Chain**

When a mira-adapters bead requires MIRA fixtures, declare a bead dependency:
```bash
bd dep add <mira-adapters-bead> <mira-fixture-gen-bead>
```

The fixture-generation bead runs first and writes fixtures to a shared path (e.g.
`/tmp/mira-fixtures/` or a shared Dolt table). The mira-adapters UAT reads from there.

Pros: natural fit with the beads workflow; explicit dependency tracking.
Cons: tight coupling between bead execution order; shared temp state is fragile.

**Option 3: Shared Live Instance**

mira-adapters UAT always runs against a live MIRA dev server. The `uat-config.yml`
in mira-adapters includes a `wait_for` pointing at the MIRA health endpoint, and the
developer is responsible for having MIRA running before UAT starts.

Pros: simplest — no fixture generation needed.
Cons: environment coupling; cannot run mira-adapters UAT in isolation; fails if
MIRA's dev server is not running.

**Recommended approach for MIRA ↔ mira-adapters:**

Use Option 3 (shared live instance) as the initial implementation since mira-adapters
does not exist yet, with a clear upgrade path to Option 1 (published fixtures) once
the adapter surface is stable. The `uat-config.yml` in mira-adapters should document
the MIRA dependency explicitly via a `depends_on` comment and a `wait_for` entry.

Design the fixture generation script in MIRA now (even if unused by mira-adapters),
so the Option 1 path is available without rearchitecting.

---

## Recommended Strategy Per Project Type

| Project type | UAT strategy | Mode | Notes |
|-------------|-------------|------|-------|
| CLI tool (installed binary) | Live-app (binary) | `smoke` | Install binary, run commands, check exit codes |
| Python library | Live-app (import) | `import_check` | Import module, call key functions |
| TypeScript/JS library | Live-app (import) | `import_check` | `node -e "require('./dist/index')"` |
| REST API (standalone) | Hybrid | `smoke` | Start server, curl key endpoints |
| Web app (full-stack) | Live-app | `playwright` | Dev server + Playwright browser tests |
| Infrastructure / config repo | Smoke | `smoke` | Validate config files, check deployed state |
| Research / design bead | Skip UAT | N/A | No artifact to test |
| FHIR IG / terminology | Import check | `import_check` | Validate JSON/YAML structure |

### Minimum UAT Config for Projects Without One

Every project that can produce PAUL-mode beads should have at minimum:

```yaml
# <project-name>: Minimum viable UAT config
project_type: cli   # or: web | library

uat_strategy:
  mode: smoke

smoke_tests:
  - cmd: "<primary-command> --version || echo 'no version flag'"
    description: "Primary tool is installed and responds"

human_in_the_loop:
  enabled: false
  skip_if_tests_pass: true
```

This ensures Phase 13 runs (even if trivially) rather than silently skipping.

---

## Fixture Generation as a Bead Phase

### Proposal

Add a fixture-generation step as an optional bead phase between implementation (Phase 5)
and UAT (Phase 13). This phase would:

1. Run a project-defined `fixture_generation` command from `uat-config.yml`
2. Write outputs to a known path (e.g. `tests/fixtures/uat-generated/`)
3. Optionally commit the fixtures to the feature branch

### uat-config.yml Extension

```yaml
fixture_generation:
  cmd: "bun run generate:uat-fixtures"
  output_dir: "tests/fixtures/uat-generated"
  commit: false  # if true, commit generated fixtures to the feature branch
  stale_check:   # optional: regenerate if older than N hours
    max_age_hours: 24
    check_cmd: "stat tests/fixtures/uat-generated/.generated_at"
```

### Phase 12.5: Fixture Generation (CONDITIONAL)

Run between Phase 12 (MoC/E2E) and Phase 13 (UAT) when `fixture_generation` is
defined in `uat-config.yml`. The orchestrator would:
1. Run `fixture_generation.cmd`
2. Verify `output_dir` is non-empty
3. If `commit: true`, create a commit with the generated fixtures
4. Pass `fixture_dir` to the UAT validator in the context block

### Decision: Defer to Implementation Bead

This feature adds orchestrator complexity during the Wave-Orchestrator Freeze period
(as of 2026-04-23). File as a follow-up bead for post-freeze implementation. Design
the `fixture_generation` key in `uat-config.yml` now so projects can declare it without
it breaking anything (the orchestrator ignores unknown keys).

---

## Summary of Key Gaps

1. 43/44 bead-tracked projects have no `uat-config.yml` → Phase 13 is a silent no-op
2. MIRA's `playwright_scenarios` are generic and not bead-aware → low signal per run
3. MIRA e2e/ test suite and uat-config.yml are disconnected → existing tests not used
4. No cross-repo fixture coordination mechanism exists
5. No fixture generation phase in the orchestrator
6. No standard for minimum viable `uat-config.yml` exists in project standards
