# UAT Fixture Strategy Standard

This standard defines when to use fixtures vs. live-app vs. hybrid UAT, how to set up
each approach, and how to configure `uat-config.yml` for new and existing projects.

See `docs/architecture/uat-audit-2026.md` for the audit findings and full design rationale.

---

## Decision Table: Which Strategy to Use

| Signal | Recommended strategy | Mode |
|--------|---------------------|------|
| Project is a CLI tool (installed binary) | Live-app (binary smoke) | `smoke` |
| Project is a Python or JS/TS library | Live-app (import check) | `import_check` |
| Project is a standalone REST API | Hybrid: live server + curl smoke | `smoke` |
| Project is a full-stack web application | Live-app: dev server + Playwright | `playwright` |
| Project is infrastructure / config only | Smoke: validate config or deployed state | `smoke` |
| Bead type is `research` / `design` / `docs` | Skip UAT — no artifact to test | N/A |
| Schema changes daily, fixtures would drift | Live-app preferred over fixtures | any |
| CI is available and can start a test server | Live-app always preferred | any |

**Default**: If uncertain, start with `smoke` and `import_check` before investing in
Playwright infrastructure.

---

## Fixture-Based UAT

Fixtures are pre-generated application state files (API response snapshots, database
seed exports, test data payloads) checked into the repo and consumed by UAT runs
without starting a live server.

### When to Use Fixtures

- The project is a library or CLI tool where the test surface is function inputs/outputs
- The API surface is stable and schema changes infrequently (< once per quarter)
- UAT needs to run offline or in parallel across multiple worktrees
- You want deterministic, fast UAT without server startup overhead

### When NOT to Use Fixtures

- The project has a complex stateful UI where rendering matters
- The API schema evolves frequently (fixtures will drift faster than you can regenerate)
- The bead being tested changes the API contract itself (fixtures would be stale before UAT runs)

### How to Set Up Fixture-Based UAT

1. **Create a fixture generation script**:
   ```bash
   # scripts/generate-uat-fixtures.sh
   #!/usr/bin/env bash
   set -euo pipefail
   FIXTURES_DIR="tests/fixtures/uat-generated"
   mkdir -p "$FIXTURES_DIR"

   # Example: capture API response
   curl -sf http://localhost:3001/api/health > "$FIXTURES_DIR/health.json"
   curl -sf http://localhost:3001/api/proposals?date=2026-01-01 > "$FIXTURES_DIR/proposals.json"

   echo "$(date -Iseconds)" > "$FIXTURES_DIR/.generated_at"
   ```

2. **Check fixtures into the repo** (or generate as part of the bead workflow):
   ```bash
   git add tests/fixtures/uat-generated/
   git commit -m "chore: regenerate UAT fixtures after schema change"
   ```

3. **Configure `uat-config.yml`** to use the fixtures:
   ```yaml
   project_type: library  # or: api

   uat_strategy:
     mode: import_check  # or: smoke (for API fixtures with mock server)

   smoke_tests:
     - cmd: "python3 -c \"import mylib; assert mylib.VERSION\""
       description: "Library imports and version is set"

   # Optional: fixture freshness check
   # fixture_generation:
   #   cmd: "bash scripts/generate-uat-fixtures.sh"
   #   output_dir: "tests/fixtures/uat-generated"
   ```

### Drift Risk Management

- Add a `# FIXTURES LAST GENERATED: <date>` comment to `uat-config.yml`
- Run fixture regeneration as part of schema migration beads
- Consider a CI job that checks fixture freshness (compare schema hash against `generated_at`)
- Never check in fixtures with hardcoded dates unless those dates are intentional test data

---

## Live-App UAT

Start the actual application (dev server, installed binary, or imported library) and
run tests against the live artifact. This is the approach used by MIRA.

### When to Use Live-App UAT

- Full-stack web applications with browser rendering requirements
- Applications where the UAT should catch rendering regressions, not just API contracts
- Projects with stable infrastructure (reliable `bun install`, predictable server startup)
- When fixtures would drift too quickly to be useful

### CLI Strategy (`project_type: cli`, `mode: smoke`)

```yaml
project_type: cli

setup:
  install:
    - "uv tool install . --force"   # or: pip install -e .
                                     # or: bun link (for Node CLI tools)

uat_strategy:
  mode: smoke

smoke_tests:
  - cmd: "<binary-name> --version"
    description: "Binary installed and version flag works"
  - cmd: "<binary-name> --help"
    description: "Help output renders without error"
  # Add 1-2 commands that exercise the core feature path:
  - cmd: "<binary-name> <key-command> --dry-run"
    description: "Core command runs (dry-run mode)"

human_in_the_loop:
  enabled: false
  skip_if_tests_pass: true
```

### Library Strategy (`project_type: library`, `mode: import_check`)

```yaml
project_type: library

setup:
  install:
    - "uv sync"   # or: bun install, npm install

uat_strategy:
  mode: import_check

smoke_tests:
  - cmd: "python3 -c \"import mylib; print(mylib.__version__)\""
    description: "Library imports and exposes version"
  - cmd: "python3 -c \"from mylib import MyClass; obj = MyClass(); print('ok')\""
    description: "Primary class instantiates without error"

human_in_the_loop:
  enabled: false
  skip_if_tests_pass: true
```

For TypeScript libraries:
```yaml
smoke_tests:
  - cmd: "node -e \"const lib = require('./dist/index'); console.log(typeof lib.myFunction)\""
    description: "Built library exports expected functions"
```

### Web Strategy (`project_type: web`, `mode: playwright`)

```yaml
project_type: web

setup:
  install:
    - "bun install"
  env:
    MY_NS: "project-name"   # portless namespace — override per-bead if needed
  wait_for: "http://project-api.localhost:1355/health"

uat_strategy:
  mode: playwright
  base_url: "http://project.localhost:1355"
  dev_server_command: "MY_NS=project-name bun run dev:all"

smoke_tests:
  - cmd: "curl -sf http://project-api.localhost:1355/health"
    description: "API health endpoint responds with 200"
  - cmd: "curl -sf http://project.localhost:1355 -o /dev/null"
    description: "Frontend root loads"

# Static scenarios are supplementary — the uat-validator derives scenarios
# from the bead's acceptance criteria. Keep these generic or domain-agnostic.
playwright_scenarios:
  - name: "app-loads"
    description: "Application loads without JavaScript errors"
    steps:
      - "Navigate to base_url"
      - "Verify page title is not empty"
      - "Verify no console errors in first 3 seconds"

human_in_the_loop:
  enabled: false
  skip_if_tests_pass: true
```

**Important note on `playwright_scenarios`**: These static steps are supplementary.
The `uat-validator` agent derives its primary UAT scenarios from the bead's acceptance
criteria (bead_description), not from these static steps. Keep static scenarios to
generic smoke checks. Bead-specific scenarios should come from the acceptance criteria.

---

## Cross-Repo Fixtures

When Project A requires fixture data from Project B for its UAT (e.g. mira-adapters
needs MIRA API response fixtures), use the following coordination pattern:

### Pattern: Shared Live Instance (recommended for initial implementation)

Configure Project A's `uat-config.yml` to depend on Project B's running server:

```yaml
# mira-adapters/.claude/uat-config.yml
project_type: library

setup:
  install:
    - "bun install"
  # DEPENDS ON: MIRA dev server must be running before UAT starts
  # Start with: cd ~/code/mira && MIRA_NS=mira bun run dev:all &
  wait_for: "http://mira-api.localhost:1355/health"

uat_strategy:
  mode: smoke

smoke_tests:
  - cmd: "curl -sf http://mira-api.localhost:1355/health"
    description: "MIRA API is reachable (cross-repo dependency)"
  - cmd: "node -e \"const adapters = require('./dist'); console.log(typeof adapters.MiraAdapter)\""
    description: "mira-adapters library exports MiraAdapter"
```

Document the cross-repo dependency explicitly in `uat-config.yml` comments and in
the bead description.

### Pattern: Published Fixtures (for stable, mature cross-repo dependencies)

1. In Project B, add a fixture generation script:
   ```bash
   # scripts/generate-uat-fixtures.sh
   # Captures API snapshots for use by downstream projects
   ```

2. Run the script as part of a bead workflow or CI job; output to `dist/uat-fixtures/`.

3. In Project A's `uat-config.yml`, fetch the fixtures during setup:
   ```yaml
   setup:
     install:
       - "bun install"
       - "mkdir -p tests/fixtures && curl -L <fixtures-url> | tar -xz -C tests/fixtures/"
   ```

Use this pattern when: the cross-repo fixture set is stable, the projects release
independently, and you want UAT to run without Project B running locally.

---

## uat-config.yml Reference

### Minimum Viable Config

Every project that can produce PAUL-mode beads (type=feature or effort=medium/large)
should have at minimum a smoke-test config. This ensures Phase 13 runs rather than
silently skipping.

```yaml
# <project-name>: Minimum viable UAT config
# Created: <date>
project_type: cli   # REQUIRED: cli | web | library

uat_strategy:
  mode: smoke       # REQUIRED: smoke | playwright | import_check

smoke_tests:
  - cmd: "<project-health-check-command>"
    description: "Project is installed and responds"

human_in_the_loop:
  enabled: false
  skip_if_tests_pass: true
```

### Full Field Reference

```yaml
project_type: cli | web | library
# Required. Selects the UAT strategy in uat-validator.

setup:
  install: ["<cmd1>", "<cmd2>"]
  # Optional. Commands run before UAT scenarios. Install deps, build, etc.

  env: {KEY: "value"}
  # Optional. Environment variables set for all UAT commands.

  wait_for: "http://host/health"
  # Optional. URL polled (curl -sf) until HTTP 200 before running UAT.
  # Use for web projects that need a server to start.

uat_strategy:
  mode: smoke | playwright | import_check
  # Required. Selects the execution strategy in uat-validator.

  base_url: "http://host:port"
  # Required for mode: playwright.

  dev_server_command: "MIRA_NS=ns bun run dev:all"
  # Required for mode: playwright. Command to start the dev server.

smoke_tests:
  - cmd: "<shell command>"
    description: "<human-readable description>"
  # Optional list. Each command must exit 0 to pass.
  # Captured as evidence; classified PASS/FAIL.

playwright_scenarios:
  - name: "scenario-name"
    description: "What this scenario verifies"
    steps:
      - "<step 1 description>"
      - "<step 2 description>"
  # Optional list. Supplementary to bead-derived scenarios.
  # Note: uat-validator derives primary scenarios from bead acceptance criteria.
  # Keep these generic (app-loads, login-works); bead-specific logic lives in AKs.

human_in_the_loop:
  enabled: false | true
  skip_if_tests_pass: true | false
  prompt: "Description of what the human should verify manually"
  # Optional (default: enabled=false, skip_if_tests_pass=true).
  # When enabled=true and skip_if_tests_pass=false: HITL gate always runs.
  # When enabled=true and skip_if_tests_pass=true: HITL gate skipped if all tests pass.

# Future (not yet implemented — see CCP follow-up bead):
# fixture_generation:
#   cmd: "bash scripts/generate-uat-fixtures.sh"
#   output_dir: "tests/fixtures/uat-generated"
#   commit: false
#   stale_check:
#     max_age_hours: 24
```

### Placement

Place `uat-config.yml` at `.claude/uat-config.yml` in the project root. The bead-orchestrator
reads it from `.claude/uat-config.yml` relative to the worktree root.

---

## Installation Checklist for New Projects

When adding UAT to a project for the first time:

- [ ] Identify `project_type` (cli | web | library)
- [ ] Write `uat-config.yml` at `.claude/uat-config.yml` using the minimum viable template
- [ ] Add at least one `smoke_test` that can be run without a live server
- [ ] For `mode: playwright`: confirm `playwright` (or `playwright-cli`) is in devDependencies
- [ ] For `mode: playwright`: test `dev_server_command` manually to confirm it starts and
      the `wait_for` URL responds within 30 seconds
- [ ] For `mode: import_check`: confirm the build output (`dist/`) exists after `setup.install`
- [ ] Test a manual UAT run: spawn `uat-validator` manually with a sample bead context
- [ ] For cross-repo dependencies: document the dependency in `uat-config.yml` comments

---

## Common Pitfalls

| Pitfall | Prevention |
|---------|-----------|
| `playwright_scenarios` contain bead-specific steps | Keep static scenarios generic; put bead-specific logic in acceptance criteria |
| Hardcoded credentials in `uat-config.yml` | Use env vars or 1Password references; never commit real secrets |
| Missing `wait_for` for web projects | Always add `wait_for` for web UAT; server startup is not instantaneous |
| Fixture dates hardcoded to past dates | Use relative dates or parameterize; hardcoded dates cause false failures |
| UAT skipping silently on PAUL-mode beads | If you see no UAT output in orchestrator logs, the project is missing `uat-config.yml` |
| Cross-repo: Project B not running when Project A UAT starts | Document the dependency in `uat-config.yml` comments and bead description |
