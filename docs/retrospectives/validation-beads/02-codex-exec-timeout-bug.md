---
title: "Codex exec timeout not propagated to agent exit code"
description: >
  When the Codex adversarial phase (Phase 9 of bead-orchestrator) exceeds its
  configured wall-clock limit, the subprocess terminates with SIGALRM but the
  orchestrator treats it as exit code 0 (success). The bead proceeds without a
  real adversarial check. Fix: capture non-zero exit codes from the Codex runner
  and surface them as a Phase 9 WARN so the orchestrator can retry or skip
  explicitly.
type: bug
effort: micro
rubric_weight: 1
expected_complexity: trivial — check returncode + surface warn
---

## Scenario

A developer dispatches a bead via `cld -b <id>`. During Phase 9 the Codex
runner is given a 60-second wall-clock limit. On a slow CI host the Codex
process is killed by SIGALRM after 60 seconds. Python's `subprocess.run`
returns a `CompletedProcess` with `returncode=-14` (SIGALRM). The orchestrator
currently checks only `stdout` for the JSON report and ignores `returncode`,
so it proceeds with an empty adversarial report as if Codex passed.

## Acceptance Criteria

- `returncode != 0` from the Codex runner causes a Phase 9 `WARN: codex timeout`
  note rather than silent success
- The orchestrator either retries once or records `codex_grade=TIMEOUT` in the
  bead metrics before continuing
- Unit test `test_codex_timeout_returncode` is green
- No changes to Codex prompt or model selection

## MoC Table

| Metric | Before | After |
|--------|--------|-------|
| Silent Codex timeout failures | unbounded | 0 |
| `codex_grade=TIMEOUT` rows in metrics | 0 | logged per timeout |

## Baseline Sketch

```python
# beads-workflow/lib/orchestrator/ingest_codex.py — before
result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
report = json.loads(result.stdout)   # silently empty on timeout

# after
result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
if result.returncode != 0:
    logger.warning("Codex runner exited %d — marking TIMEOUT", result.returncode)
    return CodexReport(grade="TIMEOUT", details=result.stderr[:500])
report = json.loads(result.stdout)
```
