---
description: Implement plan autonomously with DoD verification
argument-hint: [plan-file]
tags: project
timeout: 1800000
---

# /impl - Autonomous Implementation with DoD Verification

This command covers everything from writing code to a verified, committed result: implementation, testing, linting, documentation, and Definition of Done verification. No user interaction required.

## Workflow Position

```
plan (interactive) -> impl (autonomous) -> "session close" (ship via agent)
```

## Prerequisites

Before running `/impl`:
1. Plan exists (created by `/plan` or manually)
2. Plan has "Developer Decisions" section with resolved questions
3. Plan has "Test Plan" section defining framework and targets
4. Plan's "Recommendation" is "Ready to implement"

If prerequisites are not met, suggest running `/plan` first.

### Factory-Ready Check (optional, for bead IDs)

When running `/impl <bead-id>`, optionally run `/factory-check <bead-id>` first to verify the spec is complete enough for autonomous execution.

**If factory-ready check fails** (spec gaps detected), suggest running `/plan <bead-id>` to resolve open decisions before proceeding. The factory-ready check is a **warning, not a hard gate** — `/impl` can proceed even if the check flags gaps.

Key signals that indicate a bead needs interactive work before autonomous execution:
- Missing acceptance criteria (agent cannot determine when done)
- No MoC table (agent cannot know how to verify each AC)
- Vague or empty description (agent lacks context)
- Feature/epic missing NLSpec `intent` (unresolved design questions)
- Active blockers (dependency walls mid-execution)

These are spec quality issues (Phase 1), not implementation quality issues (Phase 4). A bead can have a perfect spec and still need debugging after implementation — these checks are about whether the spec is clear enough to start.

## Step 1: Find and Validate Plan

Locate the implementation plan:
1. If argument provided:
   a. If it looks like a bead ID (no `/`, no `.md` extension):
      → Check `malte/plans/<argument>.md`
      → If found, use it
      → If not found, try as file path (existing behavior)
   b. Otherwise, use as file path directly
2. Otherwise, find the most recent plan in `ticket/docs/`, `plans/`, or project root

**Validation checks**:
- Plan file exists
- Has "Step by Step Tasks" section
- Recommendation is "Ready to implement" (warn if not, but continue)

Read the entire plan to understand scope.

## Step 2 + 3: Implementation with TDD (Autonomous)

Implementation and testing are interleaved using TDD discipline. See `standards/workflow/tdd-discipline.md` for the full standard.

### TDD Mode (Default for Code Changes)

For each task in "Step by Step Tasks":

```
1. Read relevant files (understand current state)
2. Write failing test for the desired change               (RED)
3. Run test -> confirm it fails for the RIGHT reason       (VERIFY RED — MANDATORY GATE)
4. Commit the failing test: "test: red — <what is tested>" (COMMIT RED)
5. Write minimum production code to pass                   (GREEN)
6. Run test -> confirm it passes                           (VERIFY GREEN)
7. Run full test suite -> confirm no regressions
8. Refactor if needed -> run tests again                   (REFACTOR)
9. Commit: "feat/fix: green — <what was implemented>"      (COMMIT GREEN)
10. Mark task complete
```

**Red-Green Gate (non-negotiable):**

Step 3 is a **hard gate**. Before writing ANY production code:
- The test MUST be executed (not just written)
- The test MUST fail (exit code != 0)
- The failure MUST be for the expected reason (not import error, syntax error, or wrong test)
- You MUST cite the failure output: `"Test failed as expected: <test_name> -> <failure message>"`

If the test passes immediately (already green), it proves nothing — either the test is wrong
or the behavior already exists. Investigate before proceeding.

**Why separate RED and GREEN commits:** This creates an auditable TDD trail. The review-agent
checks commit history for Red-before-Green ordering (Phase A4: TDD Discipline). A single commit
with both test and production code signals "test-after" rather than "test-first".

### When to Skip TDD

Skip TDD and implement directly (then run existing tests) for:
- Config file changes, documentation, dependency updates
- CSS/styling, file renames/moves
- Changes with no testable behavior

When TDD is skipped, Step 3 runs as a sequential test pass after implementation.

### Sequential Mode (Non-TDD Fallback)

If the plan explicitly marks tasks as non-TDD, or if changes are purely config/docs:

1. **Track tasks explicitly** from "Step by Step Tasks" using the current harness's task-tracking facility
2. **Execute each task** in order:
   - Read relevant files before modifying
   - Make surgical changes (minimal diffs)
   - Follow existing code patterns
   - Apply decisions from "Developer Decisions" section
3. **Mark todos complete** as each step finishes
4. **Run full test suite** after all tasks complete

### Decision Handling

If an unexpected decision is needed:
- Check "Developer Decisions" section first
- If not covered, make the minimal/safest choice
- Document the choice in comments or commit message
- Do NOT stop to ask the user

### Error Handling During Implementation

If code changes cause issues:
- Attempt to fix based on error message
- If stuck after 3 attempts on same issue, skip and note in report
- Continue with remaining tasks

## Step 3: Unit Tests (if not already covered by TDD)

Execute unit tests based on the Test Plan's detected framework. If TDD mode was used in Step 2, this step verifies the full suite one final time.

### Framework-Specific Execution

| Framework | Command | Notes |
|-----------|---------|-------|
| pytest | `uv run pytest [test_file]` or `pytest [test_file]` | Use uv if available |
| Jest | `npm test` or `npx jest [test_file]` | |
| Vitest | `npx vitest run` | |
| Pester | Via project-specific test runner on remote server | Cannot run locally on non-Windows |
| ShellSpec | `cd [test_dir] && shellspec -s /bin/bash` | |
| Go | `go test ./...` | |
| Rust | `cargo test` | |
| RSpec | `bundle exec rspec [spec_file]` | |

### Test Failure Handling

If tests fail:
1. Analyze failure output
2. Attempt fix (max 3 iterations per test)
3. Re-run tests after fix
4. If still failing after 3 attempts, document in report and continue

## Step 4: Integration Tests (if defined in Test Plan)

Execute integration tests from the Test Plan to validate user-facing behavior.

**Option A: Project has a dedicated integration-test helper**
```
Invoke the configured integration-test helper.
Prompt: "Run integration tests. Test Plan: [section]. Changed files: [list]."
```

**Option B: Direct execution**
Run integration test commands listed in the Test Plan directly.

### Failure Handling
Same 3-attempt rule. Document actual vs expected if still failing.

## Step 5: Linting

Run the appropriate linter(s) for changed files:

| File Type | Linter | Command |
|-----------|--------|---------|
| Python | ruff | `ruff check [file]` |
| JavaScript/TypeScript | eslint | `npx eslint [file]` |
| PowerShell | PSScriptAnalyzer | Via project-specific runner |
| Shell/Bash | shellcheck | `shellcheck [file]` |
| Go | golangci-lint | `golangci-lint run` |
| Rust | clippy | `cargo clippy` |

Fix automatically fixable issues. Document issues requiring architectural decisions.

## Step 6: Documentation Updates

### Changelog (for user-visible behavior changes)

If the plan affects user-visible behavior:
1. Determine version tracking method
2. Add entry to appropriate changelog section
3. Use existing changelog format

Use the changelog/documentation helper if available:
```
Invoke the configured changelog/documentation helper.
```

### User Documentation

If docs need updates (from plan or test results):
1. Update relevant files in `docs/`
2. Keep changes minimal and focused

## Step 7: DoD Verification

Run Definition of Done gates to verify implementation quality. These are mandatory checks that must pass before committing.

**Verification Discipline**: Every gate follows the evidence protocol from `standards/workflow/verification-discipline.md`:

```
1. RUN:   Execute the verification command
2. READ:  Read the full output (don't skim)
3. CHECK: Verify exit code AND output content
4. CITE:  Include specific output in the report
5. DECIDE: PASS only if evidence supports it
```

Red flags that must not appear in gate reports: "should", "probably", "seems to", "I think", "likely". Every claim needs a command output or tool result as evidence.

### Gate 1: Code Review

Review changed files against quality patterns:
- **Wrapper functions**: Are external calls wrapped for testability?
- **Code reuse**: Could existing functions be extended instead of duplicating?
- **Test independence**: Do tests avoid environment-specific dependencies?
- **Return values**: Are result properties set before success checks?
- **YAGNI**: No unused parameters, return fields, or abstractions?

Load `code-review` skill if available for project-specific patterns.

**If issues found**: Fix them before proceeding.

### Gate 2: Security Review

Analyze code changes for vulnerabilities:
- No hardcoded secrets (use env vars or secret managers)
- No injection vulnerabilities (sanitize external input)
- No unsafe deserialization
- No new dependencies with known critical CVEs

**If HIGH severity issues found**: Fix them before proceeding.

### Gate 3: Test Coverage & TDD Verification

Use a dedicated test-review helper to verify:
- Unit tests exist for all new/modified functions
- Tests actually test behavior (not mock return values)
- Tests mock dependencies, not the function under test
- Tests are environment-independent

```
Invoke the configured test-review helper.
Prompt: "Verify unit tests exist and adequately cover all changed behavior.
Changed files: [list from git diff --name-only]. Report any gaps."
```

**TDD Audit (if TDD mode was used):**
Check the git log for Red-Green commit pattern:
```bash
git log --oneline | head -20
```
- Look for alternating `test:` (RED) and `feat:/fix:` (GREEN) commits
- If all tests and code appear in single commits → TDD-C (test-after pattern)
- Report TDD grade: A (clear red-green), B (tests exist, order unclear), C (test-after)

**If gaps found**: Write missing tests, then re-run verification.

### Gate 4: Documentation Consistency

Use the changelog/documentation helper to verify:
- Documentation matches actual code changes
- Changelog entries are accurate
- No inconsistencies between docs and implementation

```
Invoke the configured changelog/documentation helper.
Prompt: "Verify documentation accurately reflects code changes. Report inconsistencies."
```

**If inconsistencies found**: Fix them before proceeding.

### Gate 5: Means of Compliance (MoC) Verification

If the plan or bead contains a "Means of Compliance" table, verify all evidence is provided:

1. Parse the MoC table from the plan or bead (`bd show <id>`)
2. For each row, check:
   - `unit`/`e2e`/`integ`: Named test exists AND passes
   - `review`: Code review gate (Gate 1) passed for the relevant files
   - `demo`: Screenshot or description captured (note in report)
   - `doc`: Documentation section exists and is accurate

3. Output MoC verification:

```markdown
### MoC Verification

| # | Criterion | MoC | Evidence | Status |
|---|-----------|-----|----------|--------|
| 1 | [AK] | unit | test_foo() PASS | VERIFIED |
| 2 | [AK] | e2e | test_bar.spec.ts PASS | VERIFIED |
| 3 | [AK] | review | Gate 1 passed | VERIFIED |
| 4 | [AK] | doc | Updated in README.md | VERIFIED |
```

**Gate Logic:**
- All automated MoC (`unit`, `e2e`, `integ`) must have passing tests
- `review` is satisfied by Gate 1 (Code Review) passing
- `demo` requires a note in the report (human verifies later)
- `doc` requires the document exists and is updated
- If MoC table is missing from plan: SKIP gate with warning, do not block

**If MoC evidence is incomplete**: Write missing tests or docs, re-verify (max 3 attempts).

### Gate Failure Handling

| Gate | On Failure |
|------|-----------|
| Code Review | Auto-fix, re-check (max 3 attempts) |
| Security | Auto-fix if possible, otherwise note in report |
| Test Coverage | Write missing tests, re-verify |
| Documentation | Update docs, re-verify |
| MoC Verification | Write missing evidence, re-verify |

If a gate still fails after 3 attempts: document the issue in the final report and continue to commit. The issue will be flagged for human review.

## Step 8: Plan Completion Verification

After DoD gates pass, verify every plan item was actually implemented. This catches skipped or forgotten tasks.

**When to run**: Always when the plan has 5+ tasks. Skip for small plans (< 5 tasks).

1. Parse all tasks from the plan's "Step by Step Tasks" section
2. Spin up 2-3 explore subagents (one per task group) to verify in parallel:
   - Expected files exist and contain the planned changes
   - Tests for new behavior exist and pass
   - No plan items were silently skipped
3. Collect results and report a pass/fail summary per plan item:

```markdown
### Plan Verification

| # | Plan Task | Status | Evidence |
|---|-----------|--------|----------|
| 1 | [Task from plan] | PASS | [file exists, test passes] |
| 2 | [Task from plan] | PASS | [grep confirms change] |
| 3 | [Task from plan] | SKIP | [reason — intentional deviation] |
```

**Non-blocking**: Report findings but do NOT prevent commit. Some plan deviations are intentional decisions made during implementation.

## Step 9: Commit Changes

Create atomic commits for the implementation:

```bash
git add -A
git commit -m "$(cat <<'EOF'
<type>(<scope>): <description>

<body explaining what and why>

Refs: <TICKET-ID>
EOF
)"
```

Types: fix, feat, refactor, docs, test, chore

## Step 10: Final Report

Output implementation summary:

```
## Implementation Complete

### Changes Made
- [List of files changed with brief description]

### Implementation Mode
- **TDD**: [Yes/No/Partial] — [X cycles completed]

### Unit Tests
- **[Framework]**: [X passed, Y failed] — `[exact command] -> [exact output summary]`

### Integration Tests (if applicable)
- **[Scenario]**: [PASS/FAIL] — `[exact command] -> [exact output summary]`

### DoD Verification (with evidence)
- Code Review: [PASS/issues found] — [specific findings or "No issues in N files"]
- Security Review: [PASS/issues found] — [specific findings or "No secrets, no injection"]
- Test Coverage: [PASS/gaps found] — `[test command] -> [pass count, coverage %]`
- Documentation: [PASS/inconsistencies found] — [specific findings]
- MoC Verification: [PASS/SKIP/gaps found] — [X/Y criteria verified, missing evidence listed]

### Commits
- [Commit hash]: [Message]

### Notes
- [Any decisions made during implementation]
- [Any issues encountered and how resolved]
- [Any items skipped with reason]
- [Any DoD gates that need human review]

### Bead Update
After successful implementation, append architectural rationale to the bead:
  bd update <id> --append-notes="Approach: [brief 'why it was built this way']"

### Next
Say "session close" to push, tag, and optionally create MR/PR (spawns the configured closeout agent).
```

## Error Handling Summary

| Situation | Action |
|-----------|--------|
| Missing prerequisites | Suggest `/plan`, but continue if possible |
| Implementation error | Fix attempt (3x), then skip and note |
| Test failure | Fix attempt (3x), then document and continue |
| DoD gate failure | Fix attempt (3x), then document for human review |
| Missing decision | Make minimal/safe choice, document |

## Non-Interactive Guarantee

This command runs without user input:
- All decisions come from the plan's "Developer Decisions" section
- Test targets are pre-defined in "Test Plan" section
- DoD gates run autonomously with auto-fix attempts
- Unexpected situations handled with safe defaults
- Full report provided at the end
