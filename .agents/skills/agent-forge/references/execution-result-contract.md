# Execution-Result Contract

Use this contract when an agent-facing helper script returns more than one field, or when the caller must distinguish between successful, degraded, and failed outcomes without reparsing prose.

The rule is simple:

- Deterministic collection, parsing, polling, transformation, and aggregation belong in `scripts/`, preferably Python.
- Agent prompts own judgment, prioritization, policy, and branching decisions.
- A helper may print a bare value only when it returns exactly one atomic value with no meaningful failure modes.
- Otherwise emit the canonical JSON envelope defined in [core/contracts/execution-result.schema.json](/Users/malte/code/claude-code-plugins/core/contracts/execution-result.schema.json).

## Bare Value vs JSON

Use bare stdout for:

- A UUID from `metrics-start`
- A single path
- A count with no degraded mode

Use `execution-result` JSON for:

- Multiple fields
- Partial or degraded results
- Recoverable errors
- Any helper where the caller needs remediation guidance

## Envelope

```json
{
  "status": "ok|warning|error",
  "summary": "one-line result summary",
  "data": {},
  "errors": [],
  "next_steps": [],
  "open_items": [],
  "meta": {
    "contract_version": "1",
    "producer": "script-name",
    "generated_at": "2026-04-22T12:00:00Z",
    "schema": "core/contracts/execution-result.schema.json"
  }
}
```

## Field Semantics

- `status`: primary branch signal for the caller
- `summary`: one sentence a human can read without inspecting `data`
- `data`: structured payload the caller actually consumes
- `errors`: encountered problems with fix/continue guidance
- `next_steps`: what the caller should do next, if anything
- `open_items`: remaining unresolved work or follow-up questions
- `meta`: producer and contract provenance

## Error Guidance

If `status` is `warning` or `error`, every item in `errors` should tell the caller at least one of:

- how to fix it now: `suggested_fix`
- how to continue anyway: `continue_with`
- what is missing or blocking: `blocked_by`

This prevents orchestrators from needing a second or third tool call just to learn how to react.

## Exit Codes

For agent-facing helpers, prefer this behavior:

- Exit `0` when the script emitted a valid envelope, even if `status` is `warning` or `error`
- Exit non-zero only when the helper could not honor the contract at all, such as a crash or malformed invocation

That keeps the branching signal in JSON, not in shell error handling.

## Python Pattern

```python
#!/usr/bin/env python3
import json
from datetime import datetime, UTC


def emit(status: str, summary: str, data: dict, errors: list[dict] | None = None,
         next_steps: list[dict] | None = None, open_items: list[dict] | None = None) -> None:
    print(json.dumps({
        "status": status,
        "summary": summary,
        "data": data,
        "errors": errors or [],
        "next_steps": next_steps or [],
        "open_items": open_items or [],
        "meta": {
            "contract_version": "1",
            "producer": "example-script",
            "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "schema": "core/contracts/execution-result.schema.json",
        },
    }))
```

## Example: Degraded But Usable

```json
{
  "status": "warning",
  "summary": "Metrics unavailable; built report from bead notes and scrollback only.",
  "data": {
    "sources_used": ["bd", "git", "cmux"],
    "metrics_available": false
  },
  "errors": [
    {
      "code": "METRICS_DB_UNAVAILABLE",
      "message": "No usable wave rows were found in ~/.claude/metrics.db.",
      "suggested_fix": "Propagate run metadata into child cld sessions before the next wave.",
      "continue_with": "Use bead notes, git log, and cmux scrollback for this report."
    }
  ],
  "next_steps": [
    {
      "id": "fix-metrics-propagation",
      "summary": "Backfill WAVE_ID and RUN_ID propagation into child sessions.",
      "priority": "soon",
      "automatable": false
    }
  ],
  "open_items": [],
  "meta": {
    "contract_version": "1",
    "producer": "wave-close-report",
    "generated_at": "2026-04-22T12:00:00Z",
    "schema": "core/contracts/execution-result.schema.json"
  }
}
```

## Authoring Rule

If you find yourself writing any of the following inside an agent or skill body, stop and extract it:

- a fenced Python block with real control flow
- a 10+ line Bash block that parses and chains tools
- prose that says “run X, store it, parse it, then feed it to Y”
- inline `python -c` or heredoc glue to shape structured data

Those are helper responsibilities, not prompt responsibilities.
