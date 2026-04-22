---
name: wave-monitor
description: >-
  Long-lived Haiku subagent that polls wave completion status on behalf of the
  wave-orchestrator. Runs wave-completion.sh every 270 seconds using bash sleep,
  keeping the parent Agent() call blocked (parked) for the entire monitoring
  window. Returns a structured JSON verdict when the wave reaches a terminal
  state. Triggers on: wave monitor, poll wave, watch wave, monitor wave progress.
tools: Bash, Read
model: haiku
---

# Wave Monitor Agent

Long-lived polling agent for wave completion. The parent wave-orchestrator spawns
this agent ONCE per wave and blocks on the Agent() call until wave-monitor returns
a terminal verdict. Because this agent uses `bash sleep 270` between polls (not
ScheduleWakeup), the parent context stays parked — it is NOT re-read on every tick.

**Cost model:** Haiku at <$0.001/call vs Opus at $0.06+/call for the same check.
On a 4-hour wave with 270s intervals this saves ~88 Opus calls (~$5).

## Input Contract

The agent receives a JSON object as its prompt. Required fields:

```json
{
  "wave_config_path": "/absolute/path/to/wave-config.json",
  "stuck_threshold_hours": 4,
  "review_loop_max_iterations": 3,
  "poll_interval_seconds": 270
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `wave_config_path` | string | (required) | Absolute path to wave config JSON |
| `stuck_threshold_hours` | number | `4` | Hours before a bead in_progress → stuck |
| `review_loop_max_iterations` | number | `3` | Codex review iterations before review-loop verdict |
| `poll_interval_seconds` | number | `270` | Seconds to sleep between polls (default 270 ≤ 5-min cache TTL) |

Wave config JSON shape (as written by wave-dispatch.sh):

```json
{
  "wave_id": "wave-abc123",
  "dispatch_time": "2026-04-21T10:00:00",
  "beads": [
    {"id": "CCP-abc", "surface": "surface:3"},
    {"id": "CCP-def", "surface": "surface:5"}
  ]
}
```

## Return Contract

On ANY terminal condition, return a JSON object to stdout and exit. The parent
wave-orchestrator reads this output.

### Outcome 1: complete

All beads closed, all panes idle.

```json
{
  "status": "complete",
  "summary": {
    "bead_count": 4,
    "elapsed_minutes": 87,
    "polls_run": 20
  }
}
```

### Outcome 2: needs_intervention — pane-error

One or more panes show error/crash signals that are not recoverable by monitoring.

```json
{
  "status": "needs_intervention",
  "reason": "pane-error",
  "bead_id": "CCP-abc",
  "details": "Pane surface:3 shows: ECONNREFUSED / fatal / panic at tail-5"
}
```

### Outcome 3: needs_intervention — stuck

A bead has been `in_progress` for longer than `stuck_threshold_hours` with
no surface activity and no recent agent_calls in metrics.db.

```json
{
  "status": "needs_intervention",
  "reason": "stuck",
  "bead_id": "CCP-abc",
  "details": "Bead in_progress for 5.2h (threshold: 4h). Surface idle. No recent agent_calls."
}
```

### Outcome 4: needs_intervention — review-loop

Parsed scrollback from a pane shows >= `review_loop_max_iterations` Codex review
iteration lines (pattern: "Review iteration N/M" or "Codex review iteration N").

```json
{
  "status": "needs_intervention",
  "reason": "review-loop",
  "bead_id": "CCP-abc",
  "details": "Detected 3 review iterations in pane scrollback (threshold: 3)."
}
```

### Outcome 5: needs_intervention — ambiguous

wave-completion.sh itself errored (exit code 2), or JSON output was unparseable,
or the wave config file was not found.

```json
{
  "status": "needs_intervention",
  "reason": "ambiguous",
  "bead_id": null,
  "details": "wave-completion.sh exited with code 2. stderr: <captured>"
}
```

## Polling Workflow

```
PARSE input JSON → extract wave_config_path, thresholds, poll_interval_seconds
VERIFY wave_config_path exists (if not → return ambiguous immediately)

LOOP:
  RUN wave-completion.sh $wave_config_path → capture stdout + stderr + exit_code

  IF exit_code == 2 OR stdout is not valid JSON:
    RETURN needs_intervention(ambiguous) with stderr

  PARSE completion JSON:
    complete=true → RETURN complete verdict

    stragglers present:
      FOR EACH straggler:
        IF bd_status == in_progress AND elapsed > stuck_threshold_hours:
          RETURN needs_intervention(stuck)

    stalls array non-empty:
      RETURN needs_intervention(stuck) for first stall entry

  CHECK pane scrollback for each bead surface (via wave-completion output or direct read):
    IF any surface shows error/panic/fatal/ECONNREFUSED at tail:
      RETURN needs_intervention(pane-error)

    IF review_loop_max_iterations reached in any surface:
      RETURN needs_intervention(review-loop)

  SLEEP poll_interval_seconds via: bash -c "sleep <N>"

END LOOP
```

## Implementation

> **Extracted to helper:** All polling logic lives in
> `beads-workflow/scripts/wave-poll.py`. This section is now a thin
> dispatch wrapper — see `wave-poll.py` for the full implementation.

```bash
# Parse input JSON
INPUT="$ARGUMENTS"
WAVE_CONFIG=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['wave_config_path'])")
STUCK_HOURS=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('stuck_threshold_hours', 4))")
REVIEW_MAX=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('review_loop_max_iterations', 3))")
POLL_SEC=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('poll_interval_seconds', 270))")

# Discover wave-poll.py
SCRIPT=$(find ~/.claude -name "wave-poll.py" 2>/dev/null | head -1)
SCRIPT="${SCRIPT:-$(find . -name "wave-poll.py" 2>/dev/null | head -1)}"

# Delegate all polling logic to the helper and print its verdict
python3 "$SCRIPT" \
  --config "$WAVE_CONFIG" \
  --stuck-hours "$STUCK_HOURS" \
  --review-max "$REVIEW_MAX" \
  --poll-interval "$POLL_SEC"
```

## Escalation Heuristics

| Signal | Verdict | Notes |
|--------|---------|-------|
| `complete=true` in wave-completion.sh output | `complete` | All beads closed + all panes idle |
| `stalls` array non-empty | `stuck` | wave-completion.sh already detected stall |
| Straggler `in_progress` > stuck_threshold_hours | `stuck` | Based on bd updated_at |
| Pane tail shows error/panic/fatal/traceback | `pane-error` | Excludes dead-pane error messages |
| Review iteration count >= review_loop_max_iterations | `review-loop` | Parsed from cmux scrollback |
| wave-completion.sh exit code 2 or non-JSON output | `ambiguous` | With captured stderr |
| wave_config_path file missing | `ambiguous` | Immediate return |

## Integration with wave-orchestrator

The parent wave-orchestrator replaces its Phase 5 polling loop with a single blocking call:

```python
result = Agent(
    subagent_type="beads-workflow:wave-monitor",
    prompt=json.dumps({
        "wave_config_path": "/tmp/wave-abc123.json",
        "stuck_threshold_hours": 4,
        "review_loop_max_iterations": 3,
        "poll_interval_seconds": 270
    })
)
verdict = json.loads(result)
# verdict.status: complete | needs_intervention
```

The parent parks (context not re-read) until wave-monitor returns. Intervention verdicts
are handled by the parent — wave-monitor never remediates, only observes and reports.

## Design Constraints

- **No Write tool** — wave-monitor is read-only. Cannot mutate bead state.
- **No ScheduleWakeup** — would exit the Agent() call early, breaking the parent park.
- **Single invocation** — spawned once per wave, not once per poll.
- **bash sleep for polling** — keeps subagent alive between checks.
- **Intervention returns** — wave-monitor does not retry or fix. It returns the verdict
  and the parent decides remediation strategy.

## Fleet Inventory (CCP-6up.5)

Documents what was extracted, what was classified as ALLOWED, and why.

### Extracted to helper

| Agent / Skill | Location in prompt | Extracted to | Classification |
|---|---|---|---|
| `wave-monitor.md` `## Implementation` (115 lines bash) | Lines 168–285 (pre-refactor) | `beads-workflow/scripts/wave-poll.py` | EXTRACT — deterministic workflow logic with multiple exit paths, non-trivial JSON parsing, cmux calls |
| `bead-orchestrator.md` Phase 6 + Phase 8 `auto_decisions` SQL snippet | Two identical `python3 -c "import sqlite3..."` blocks | `increment_auto_decisions()` in `beads-workflow/lib/orchestrator/metrics.py` | EXTRACT — duplicated SQL; belongs in the metrics library alongside `start_run`, `rollup_run` |

### Classified as ALLOWED (embedded snippet permitted)

| Agent / File | Location | Snippet | Reason ALLOWED |
|---|---|---|---|
| `core/agents/session-close.md` | Line 210 | `python3 -c "import os; print(os.path.relpath...)"` | Single-value, no branching/failure contract → bare stdout output, no execution-result envelope needed |
| `meta/agents/learning-extractor.md` | Lines 261–272 | Multi-line `python3` state update for `processing-state.json` | Ad-hoc instructional fragment, not a harness workflow. Stateful side-effect with no caller-facing output contract; extraction adds no value |
| `core/agents/session-close-handlers/phase-b-close-beads.sh` | Whole file | Shell script | Shell script file, NOT an agent prompt — out of scope per bead definition |
