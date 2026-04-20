---
name: bug-triage
description: >-
  Structured 4-phase bug investigation: Reproduce → Root Cause → Fix → Regression Test.
  Use when a bug is reported, something is broken, "geht nicht", Fehler, regression detected,
  or kaputt. Guides through systematic investigation instead of guessing.
---

# Bug Triage

Systematic 4-phase workflow for diagnosing and fixing bugs. Prevents premature action by enforcing investigation before execution.

## When to Use

Trigger on: bug, broken, kaputt, geht nicht, Fehler, regression, something is wrong, doesn't work, it's broken.

Do NOT use for: feature requests, performance improvements, or refactoring unrelated to a defect.

## Phase 1: Reproduce

<investigation>
Verify the bug actually exists before analyzing causes.

1. Identify the exact reproduction steps from the bug report.
2. Set up the environment as described (OS, version, dependencies).
3. Execute the exact failing command or action.
4. Observe the actual behavior vs. expected behavior.
5. Confirm: does the bug occur consistently or intermittently?

**If not reproducible:**
- Do not guess or assume a cause.
- Do not assume — ask for more information.
- Request all of:
  - Exact error message (full traceback, not paraphrased)
  - Steps to reproduce (numbered, precise)
  - Environment details (OS, Python/Node version, dependencies)
  - Relevant logs from `~/.claude/events.db` or application logs
- Say: "I cannot reproduce this bug with the information provided. Please share [specific items]."
- Wait for the additional information before proceeding to Phase 2.
</investigation>

## Phase 2: Root Cause

<investigation>
Analyze the confirmed bug to find its root cause. Consult historical data first.

### Step 1: Query buglog.json

Load the project's bug history via `malte/hooks/buglog.py`:

```python
import sys
# NOTE: "malte/hooks" is a relative path — CWD must be the repo root when running this.
# Alternative: use Path(__file__).resolve().parent to derive an absolute path.
sys.path.insert(0, "malte/hooks")
from buglog import load_buglog, search_buglog

entries = load_buglog(cwd=".")
matches = search_buglog(entries, query="<error message or symptom>")
for m in matches:
    print(m["error_pattern"], "→", m["root_cause"], "→", m["fix"])
```

WHY: buglog.json contains past bug fixes for this project. Identical or similar bugs may have been fixed before — skip re-investigation.

### Step 2: Query events.db for recent errors

```bash
sqlite3 ~/.claude/events.db "
  SELECT substr(timestamp,1,19)||'Z', json_extract(metadata,'$.error') as err, tool
  FROM events
  WHERE event_type = 'error'
    AND date(timestamp) >= date('now', '-7 days')
  ORDER BY timestamp DESC LIMIT 20
"
```

WHY: events.db shows what tools were used and when errors occurred. Correlate timestamps with the reported bug.

### Step 3: Query open-brain for past context

```
mcp__open-brain__search(query="<error message or symptom>")
```

WHY: open-brain stores cross-project memories and learnings. A similar bug may have been encountered in a different project or session.

If open-brain is unavailable (MCP server down or timeout), skip this step gracefully and continue with synthesis — do not let a missing MCP server block the investigation.

**Fallback paths:**
- If buglog.json is missing or empty, skip Step 1 and go directly to Step 2 (events.db).
- If events.db is missing, skip Step 2 and go directly to Step 3 (open-brain).
- If open-brain is unavailable, skip Step 3 and go directly to Step 4 (synthesis).
- If all three are absent, proceed with manual code investigation based on the reproduction from Phase 1.

### Step 4: Synthesize

After querying all three data sources, form a hypothesis:
- What line/function is the defect in?
- What condition triggers it?
- Is it a regression (recently introduced)?
</investigation>

## Phase 3: Fix

<execution>
Implement a minimal fix. One concern only: fix the bug.

**Rules:**
- No cleanup, no refactoring, no opportunistic improvements.
- Touch only the files necessary to fix the confirmed root cause.
- If tempted to improve surrounding code → create a refactoring note and do not act on it now:
  ```bash
  bd create --title="[REFACTOR] <short description>" --type=task --priority=3
  ```
- One commit, one concern.

**Non-trivial fix detection:**
A fix is non-trivial if it:
- Touches more than one file (multiple files modified), OR
- Requires structural changes (interface change, new abstraction, schema migration)

If non-trivial → create a bead BEFORE implementing:

```bash
bd create --title="[BUG] <short description of bug>" --type=task --priority=1
```

Then proceed with the fix, referencing the bead ID in the commit message.
</execution>

## Phase 4: Regression Test

<execution>
Write a test that encodes the bug as a permanent guard.

### Step 1: Write the regression test

The test must:
- **Fail without the fix** (confirms the test catches the bug)
- **Pass with the fix** (confirms the fix addresses the bug)

Name the test `test_regression_<bug_description>` or `test_fix_<bead_id>`.

Add a comment above the test explaining what bug it guards against.

### Step 2: Verify test behavior

```bash
# Temporarily revert the fix (or comment it out) and run the test:
uv run pytest tests/ -k "test_regression_" -v
# Must FAIL here

# Restore the fix:
uv run pytest tests/ -k "test_regression_" -v
# Must PASS here
```

### Step 3: Run the full test suite

```bash
uv run pytest tests/ -v --timeout=30
```

WHY: Running only the new test misses side effects. The full test suite detects regressions introduced by the fix.

If any existing tests fail → diagnose before committing. The fix must not break existing behavior.
</execution>

## Out of Scope

- Performance tuning unrelated to a defect
- Feature additions discovered during investigation
- Refactoring "while we're in here"
- Bugs in external dependencies (fork or workaround instead)

## Reference

- buglog hook: `malte/hooks/buglog.py` — `search_buglog()`, `load_buglog()`, `write_backlink()`
- Event log skill: `/event-log` — query `~/.claude/events.db`
- open-brain: `mcp__open-brain__search` — cross-project memory search
- Beads CLI: `bd create --title="..." --type=task --priority=1`
