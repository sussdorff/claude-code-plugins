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

```bash
#!/usr/bin/env bash
# Parse input JSON from $ARGUMENTS (passed as inline JSON string)
# Defaults applied if fields are absent

INPUT="$ARGUMENTS"

WAVE_CONFIG=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['wave_config_path'])")
STUCK_HOURS=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('stuck_threshold_hours', 4))")
REVIEW_MAX=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('review_loop_max_iterations', 3))")
POLL_SEC=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('poll_interval_seconds', 270))")

if [[ ! -f "$WAVE_CONFIG" ]]; then
  python3 -c "import json; print(json.dumps({'status':'needs_intervention','reason':'ambiguous','bead_id':None,'details':'wave_config_path not found: $WAVE_CONFIG'}))"
  exit 0
fi

# Find wave-completion.sh relative to this agent (or from skills dir)
SCRIPT_DIR=$(find ~/.claude -name "wave-completion.sh" 2>/dev/null | head -1)
SCRIPT_DIR="${SCRIPT_DIR:-$(find . -name "wave-completion.sh" 2>/dev/null | head -1)}"

POLLS=0

while true; do
  POLLS=$((POLLS + 1))

  STDERR_FILE=$(mktemp)
  STDOUT=$(bash "$SCRIPT_DIR" "$WAVE_CONFIG" 2>"$STDERR_FILE") || EXIT_CODE=$?
  EXIT_CODE="${EXIT_CODE:-0}"
  STDERR_CONTENT=$(cat "$STDERR_FILE")
  rm -f "$STDERR_FILE"

  # exit code 2 = error
  if [[ "$EXIT_CODE" == "2" ]]; then
    python3 -c "import json; print(json.dumps({'status':'needs_intervention','reason':'ambiguous','bead_id':None,'details':'wave-completion.sh exited 2. stderr: $STDERR_CONTENT'}))"
    exit 0
  fi

  # Validate JSON
  if ! echo "$STDOUT" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
    python3 -c "import json; print(json.dumps({'status':'needs_intervention','reason':'ambiguous','bead_id':None,'details':'wave-completion.sh output not valid JSON'}))"
    exit 0
  fi

  COMPLETE=$(echo "$STDOUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('complete', False))")
  if [[ "$COMPLETE" == "True" ]]; then
    ELAPSED=$(echo "$STDOUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print('?')" 2>/dev/null || echo "?")
    python3 -c "import json; print(json.dumps({'status':'complete','summary':{'polls_run':$POLLS,'elapsed_minutes':'?'}}))"
    exit 0
  fi

  # Check for stuck beads (stalls array)
  STALL_ID=$(echo "$STDOUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
stalls = d.get('stalls', [])
if stalls:
    print(stalls[0]['id'])
" 2>/dev/null || true)
  if [[ -n "$STALL_ID" ]]; then
    python3 -c "import json; print(json.dumps({'status':'needs_intervention','reason':'stuck','bead_id':'$STALL_ID','details':'Stall detected by wave-completion.sh'}))"
    exit 0
  fi

  # Check stragglers for stuck-by-hours
  STUCK_ID=$(echo "$STDOUT" | python3 -c "
import sys, json, subprocess, datetime, re
d = json.load(sys.stdin)
stuck_hours = $STUCK_HOURS
for s in d.get('stragglers', []):
    if s.get('bd_status') == 'in_progress':
        result = subprocess.run(['bd', 'show', s['id']], capture_output=True, text=True)
        # Try to find updated_at from bd show output
        m = re.search(r'Updated: (\d{4}-\d{2}-\d{2})', result.stdout)
        if m:
            updated = datetime.datetime.strptime(m.group(1), '%Y-%m-%d')
            elapsed_h = (datetime.datetime.utcnow() - updated).total_seconds() / 3600
            if elapsed_h >= stuck_hours:
                print(f\"{s['id']}:{elapsed_h:.1f}\")
                break
" 2>/dev/null || true)
  if [[ -n "$STUCK_ID" ]]; then
    BEAD_PART="${STUCK_ID%%:*}"
    ELAPSED_PART="${STUCK_ID##*:}"
    python3 -c "import json; print(json.dumps({'status':'needs_intervention','reason':'stuck','bead_id':'$BEAD_PART','details':'Bead in_progress for ${ELAPSED_PART}h (threshold: ${STUCK_HOURS}h). Surface idle.'}))"
    exit 0
  fi

  # Check pane scrollback for error / review-loop signals
  BEAD_COUNT=$(python3 -c "import sys,json; print(json.load(open('$WAVE_CONFIG'))['beads'].__len__())")
  for i in $(seq 0 $((BEAD_COUNT - 1))); do
    SURFACE=$(python3 -c "import json; d=json.load(open('$WAVE_CONFIG')); print(d['beads'][$i]['surface'])")
    BEAD_ID=$(python3 -c "import json; d=json.load(open('$WAVE_CONFIG')); print(d['beads'][$i]['id'])")

    TAIL=$(cmux read-screen --surface "$SURFACE" --lines 10 2>&1 || true)

    # Pane error check
    if echo "$TAIL" | grep -qiE "error|panic|fatal|traceback|ECONNREFUSED|ENOENT" 2>/dev/null; then
      if ! echo "$TAIL" | grep -qE "invalid_params|not a terminal|Surface.*not found"; then
        DETAIL=$(echo "$TAIL" | grep -iE "error|panic|fatal|traceback|ECONNREFUSED|ENOENT" | tail -1 | head -c 120)
        python3 -c "import json; print(json.dumps({'status':'needs_intervention','reason':'pane-error','bead_id':'$BEAD_ID','details':'$DETAIL'}))"
        exit 0
      fi
    fi

    # Review-loop check
    SCROLLBACK=$(cmux read-screen --surface "$SURFACE" --scrollback --lines 100 2>&1 || true)
    REVIEW_COUNT=$(echo "$SCROLLBACK" | grep -cE "Review iteration [0-9]+|Codex review iteration [0-9]+" 2>/dev/null || echo "0")
    if [[ "${REVIEW_COUNT:-0}" -ge "$REVIEW_MAX" ]]; then
      python3 -c "import json; print(json.dumps({'status':'needs_intervention','reason':'review-loop','bead_id':'$BEAD_ID','details':'Detected $REVIEW_COUNT review iterations (threshold: $REVIEW_MAX)'}))"
      exit 0
    fi
  done

  # Non-terminal — sleep and poll again
  bash -c "sleep $POLL_SEC"
done
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
