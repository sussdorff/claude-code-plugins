# Bead Orchestrator Forced-Path Fixtures

These four fixtures exercise the conditional branches of the flat 0–16 orchestrator.
Each fixture documents: setup, expected execution trace, and verification criteria.

---

## Fixture A — Happy Path

### Purpose

Verify that when all agents return clean results the orchestrator completes without
spawning any conditional phases (8, 10, 11) and closes normally.

### Setup

1. Create a minimal bead with a single trivial acceptance criterion:
   ```bash
   bd create --title="Add greeting helper" --type=task \
     --description="Add a get_greeting(name) function that returns 'Hello, <name>!'" \
     --metadata='{"effort":"small"}'
   AK: "get_greeting('World') returns 'Hello, World!'"
   ```

2. Use mock review response (or let the real review-agent run against the trivial change).
   Acceptable shortcut: set `--skip-review` flag only if testing non-review conditional logic;
   for a full happy-path run, let the real agents execute.

3. Implementation: add a one-liner Python function + a passing unit test.
   The implementation MUST commit both a red and a green commit.

### Expected Execution Trace

```
Phase 0   — sizing: small task, run_id created, bd claim
Phase 1   — standards: none found (or stdlib standards only)
Phase 2   — break analysis: no risks; module impact: 1 new file
Phase 3   — architecture review: SKIPPED (S bead)
Phase 4   — standards preamble: built (empty or stdlib)
Phase 5   — implementation: Sonnet subagent; 1 red + 1 green commit
Phase 6   — review: Opus review-agent → CLEAN; Axis B NOT triggered
Phase 7   — Codex adversarial: codex-exec.sh → LGTM
Phase 8   — SKIPPED (Phase 7 returned LGTM)
Phase 9   — verification: Opus verification-agent → VERIFIED
Phase 10  — SKIPPED (Phase 9 VERIFIED)
Phase 11  — SKIPPED (Phase 10 not run)
Phase 12  — SKIPPED (no e2e/demo MoC)
Phase 13  — SKIPPED (GSD mode: type=task)
Phase 14  — constraint-checker: PASS
Phase 15  — changelog-updater: entry added
Phase 16  — rollup_run; core:session-close spawned
```

### Verification Criteria

1. `agent_calls` table has entries with `phase_label` values: `implementation`, `review`,
   `codex-adversarial`, `verification` — all keyed by the same `run_id`.
2. `agent_calls` has NO rows with `phase_label` in (`codex-fix-check`, `verification-fix`).
3. `bead_runs` row for this `run_id` has `auto_decisions = 0`.
4. Bead notes contain `"Review: status=CLEAN"` and NOT `"DECISION: auto-accept"`.
5. `rollup_run` completed: `bead_runs.codex_total_tokens > 0` (from Phase 7).
6. Session-close spawned: branch merged to main, bead closed.

---

## Fixture B — Codex Regression Path

### Purpose

Verify that when Codex adversarial review returns REGRESSION findings, Phase 8
(Opus fix + Codex re-check) runs and both `codex-adversarial` and `codex-fix-check`
rows appear in `agent_calls`.

### Setup

1. Create a bead that introduces an obvious off-by-one bug:
   ```bash
   bd create --title="Add index helper" --type=task \
     --description="Add get_nth(lst, n) that returns the nth element (1-indexed)" \
     --metadata='{"effort":"small"}'
   AK: "get_nth([10, 20, 30], 1) returns 10"
   AK: "get_nth([10, 20, 30], 3) returns 30"
   ```

2. Implement with a deliberate off-by-one: `return lst[n]` instead of `return lst[n-1]`.
   The unit test for AK2 will pass, but AK1 will return `20` not `10`.

3. Alternatively, prime Codex to detect the bug by including this in the adversarial
   prompt context: the Phase 7 prompt passes the actual git diff which will contain the
   off-by-one, and a real Codex adversarial pass should flag it as a REGRESSION.

### Expected Execution Trace

```
Phase 0–7 as in Fixture A, but:

Phase 7   — Codex adversarial: REGRESSION found
            Output contains: "REGRESSION: helpers.py:3 — get_nth uses 0-indexed n, should be n-1"

Phase 8   — RUNS:
  8a) Opus fix-agent: spawned with REGRESSION findings; fixes off-by-one; commits fix
  8b) Codex re-check: codex-exec.sh PHASE_LABEL=codex-fix-check → VERIFIED

Phase 9   — verification: Opus verification-agent → VERIFIED
Phases 10/11 — SKIPPED
Phases 12–16 — normal
```

### Verification Criteria

1. `agent_calls` has a row with `phase_label = 'codex-adversarial'` for this `run_id`.
2. `agent_calls` has a row with `phase_label = 'codex-fix-check'` for this `run_id`.
3. `agent_calls` has a row with `phase_label = 'codex-fix'` (the Opus fix-agent) for this `run_id`.
4. `bead_runs.codex_runs >= 2` after `rollup_run` (one for adversarial, one for re-check).
5. Git log shows a commit matching `"fix(<bead-id>): address codex adversarial findings"`.
6. Bead notes contain NO `"DECISION: auto-accept codex"` entry (re-check returned VERIFIED).

### Variant B2 — Still-Broken After Fix (Axis B triggered)

If the Codex re-check returns `STILL-BROKEN` (e.g. the fix was incomplete):

1. `bead_runs.auto_decisions = 1` (Axis B triggered in Phase 8).
2. Bead notes contain `"DECISION: auto-accept codex at iter 1, still-broken after fix"`.
3. Session proceeds to Phase 9 despite the unresolved finding.

---

## Fixture C — Verification Auto-Fix Path

### Purpose

Verify Phase 10 (Opus verification-fix) and Phase 11 (verification re-run) execute
when the verification-agent returns DISPUTED with `fixability=auto`.

### Setup

1. Create a bead that violates a naming standard in a machine-fixable way:
   ```bash
   bd create --title="Add config loader" --type=task \
     --description="Add load_config() that reads config.yaml and returns a dict" \
     --metadata='{"effort":"small"}'
   AK: "load_config() returns {'debug': false} when config.yaml contains debug: false"
   ```

2. Create a project standard that mandates snake_case for all function names.
   Implement the function as `loadConfig()` (camelCase) in the commit.
   Set `standards_applied` to include the naming standard path.

3. This triggers: verification-agent reads the standard, finds the naming violation,
   returns `DISPUTED` with `fixability=auto`.

### Expected Execution Trace — Success Variant (C1)

```
Phase 9  — verification: DISPUTED
           PROVENANCE-STANDARDS: naming-standard.md
           VIOLATION: loadConfig should be load_config (snake_case required)
           fixability: auto

Phase 10 — RUNS: Opus verification-fix
           Renames loadConfig → load_config in source + tests
           Commits: "fix(<bead-id>): address auto-fixable verification disputes"

Phase 11 — RUNS: Opus verification-agent re-run
           Result: VERIFIED (naming now correct)

Phase 12–16 — normal
```

### Verification Criteria (C1 Success)

1. `agent_calls` has rows for `phase_label` in (`verification`, `verification-fix`) for this `run_id`.
2. A third row exists for phase 11 re-run: `agent_calls` has two rows with `phase_label = 'verification'`.
3. Bead notes do NOT contain `"hard VETO"`.
4. Git log shows `"fix(<bead-id>): address auto-fixable verification disputes"` commit.
5. Session proceeds to Phase 12 and completes normally.

### Expected Execution Trace — Failure Variant (C2 — still DISPUTED after fix)

```
Phase 10 — RUNS: Opus verification-fix (applies fix, but fix is incomplete or wrong)

Phase 11 — RUNS: Opus verification-agent re-run
           Result: still DISPUTED

           Hard VETO triggered:
           bd update → "Verification re-run still DISPUTED after auto-fix — hard VETO."
           Report to user: bead left in_progress
```

### Verification Criteria (C2 Failure)

1. Two `phase_label = 'verification'` rows in `agent_calls`.
2. One `phase_label = 'verification-fix'` row in `agent_calls`.
3. Bead remains `status = in_progress`.
4. Bead notes contain `"hard VETO"`.
5. No session-close spawned; branch NOT merged to main.

---

## Fixture D — Human Veto Path

### Purpose

Verify that when the verification-agent returns DISPUTED with `fixability=human`,
Phase 10 is NOT spawned (hard VETO immediately), and the bead stays in_progress.

### Setup

1. Create a bead that violates an ADR requiring all database access to go through
   a repository layer (not direct SQL in handlers):
   ```bash
   bd create --title="Add user count endpoint" --type=task \
     --description="GET /users/count returns JSON {count: N} from users table" \
     --metadata='{"effort":"small"}'
   AK: "GET /users/count returns 200 with {\"count\": N}"
   ```

2. Create `docs/adr/0001-repository-pattern.md` stating: "All database queries MUST go
   through repository classes. Direct SQL in route handlers is prohibited."
   Set `adrs_in_scope` to include this ADR path.

3. Implement the endpoint with direct SQL in the handler (violating the ADR).

4. This triggers: verification-agent reads ADR, finds the direct SQL, returns DISPUTED
   with `fixability=human` (ADR violations are architectural decisions requiring human judgment).

### Expected Execution Trace

```
Phase 9  — verification: DISPUTED
           PROVENANCE-ADR: docs/adr/0001-repository-pattern.md
           CONTRADICTION: handler uses direct SQL, ADR mandates repository pattern
           fixability: human

           Hard VETO triggered immediately:
           bd update → "VETO: verification DISPUTED with fixability=human. Human review required."
           Report to user: bead left in_progress

Phase 10 — NOT spawned (fixability=human blocks)
Phase 11 — NOT spawned (Phase 10 not run)
Phases 12–16 — NOT run (hard VETO stops pipeline)
```

### Verification Criteria

1. `agent_calls` has exactly ONE `phase_label = 'verification'` row for this `run_id`.
2. `agent_calls` has ZERO rows with `phase_label = 'verification-fix'` for this `run_id`.
3. `agent_calls` has ZERO rows with `phase_label` matching the second verification re-run.
4. Bead remains `status = in_progress`.
5. Bead notes contain `"VETO: verification DISPUTED with fixability=human"`.
6. No session-close spawned; branch NOT merged to main.
7. User receives escalation message: "Verification VETO — one or more disputed items require human judgment."

---

## Running Fixtures

### Automated Check Script

After running a fixture, query the agent_calls table to verify the expected rows:

```bash
# Check agent_calls for a specific run_id
python3 - <<'EOF'
import sqlite3
from pathlib import Path

run_id = "<PASTE_RUN_ID_HERE>"
db = Path.home() / ".claude" / "metrics.db"
conn = sqlite3.connect(str(db))
conn.row_factory = sqlite3.Row

rows = conn.execute(
    "SELECT phase_label, agent_label, model, total_tokens, exit_code FROM agent_calls WHERE run_id = ? ORDER BY id",
    (run_id,)
).fetchall()

print(f"agent_calls for run_id={run_id}:")
for r in rows:
    print(f"  {r['phase_label']:30s}  {r['agent_label']:25s}  tokens={r['total_tokens']:,}  exit={r['exit_code']}")

run = conn.execute("SELECT * FROM bead_runs WHERE run_id = ?", (run_id,)).fetchone()
if run:
    print(f"\nbead_runs:")
    print(f"  auto_decisions={run['auto_decisions']}  codex_runs={run['codex_runs']}  codex_total_tokens={run['codex_total_tokens']:,}")
conn.close()
EOF
```

### Notes

- All fixtures require a running Dolt server and beads DB (`bd prime` to verify).
- Fixtures A and B can be run without real Codex access by pre-staging git commits
  with the expected bug patterns.
- Fixture C requires a real standard file; create it in `.claude/standards/` before running.
- Fixture D requires a real ADR file in `docs/adr/`; create it before running.
- For validation-mode testing: append `--validation-mode=true` to the orchestrator invocation
  and verify the `[VALIDATION]` tag appears in bead notes with no merge/push.
