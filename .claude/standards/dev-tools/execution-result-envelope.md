# Execution-Result Envelope Contract

> **Scope**: claude-code-plugins — applies to all agent-facing helper scripts.

Helpers that return more than one field, or that must distinguish `ok` / `warning` / `error` outcomes, emit the canonical envelope defined in `core/contracts/execution-result.schema.json`. Single atomic values (a UUID, a path, a count, a boolean) may print bare.

## Decision Table

| Output shape | Emit |
|--------------|------|
| Single atomic value, no meaningful failure modes | Bare stdout |
| Multiple fields | Envelope |
| Partial / degraded result the caller must detect | Envelope |
| Recoverable error the caller can route on | Envelope |

## Envelope Shape

```json
{
  "status": "ok|warning|error",
  "summary": "one-sentence human-readable result",
  "data": {},
  "errors": [],
  "next_steps": [],
  "open_items": [],
  "meta": {
    "contract_version": "1",
    "producer": "script-name",
    "generated_at": "2026-04-23T09:00:00Z",
    "schema": "core/contracts/execution-result.schema.json"
  }
}
```

Every item in `errors` should give the caller at least one of: `suggested_fix`, `continue_with`, or `blocked_by`. This prevents orchestrators from needing a second tool call just to learn how to react.

## Exit-Code Convention

- **Exit 0** when the script emitted a valid envelope — even if `status` is `warning` or `error`
- **Non-zero exit** only when the helper could not honor the contract at all (crash, malformed invocation, schema violation)

Branching belongs in JSON (`status`), not in shell error handling.

## Reference Implementation

`beads-workflow/scripts/wave-poll.py` — emits the envelope for wave-completion polling. Copy this shape when writing a new helper.

## Python Emit Helper

```python
import json
from datetime import datetime, UTC

def emit(status, summary, data, errors=None, next_steps=None, open_items=None, producer="my-script"):
    print(json.dumps({
        "status": status,
        "summary": summary,
        "data": data,
        "errors": errors or [],
        "next_steps": next_steps or [],
        "open_items": open_items or [],
        "meta": {
            "contract_version": "1",
            "producer": producer,
            "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "schema": "core/contracts/execution-result.schema.json",
        },
    }))
```

## Canonical Homes

- **Schema (machine contract):** `core/contracts/execution-result.schema.json` (+ `core/contracts/README.md`)
- **Authoring spec (prose):** `meta/skills/agent-forge/references/execution-result-contract.md` — field semantics, worked examples including degraded-but-usable case
- **Validator usage in tests:** `tests/test_agent_forge_validate_agent.py`, `tests/test_skill_auditor_validate_skill.py`, `beads-workflow/scripts/tests/test_wave_poll.py`

## Relation to Script-First Rule

The Envelope is *what* a script emits; the Script-First Rule (`dev-tools/script-first-rule`) is *where the script has to live* (in `scripts/` or `beads-workflow/lib/orchestrator/`, not inline in a skill body). Applied together they eliminate "run X, parse the text, check if empty, run Y" prose from skill/agent bodies — the skill says `$SCRIPT` and branches on `status`.

## Authoring Rule

If you find yourself writing any of the following inside a skill or agent body, stop and extract it to a script that emits this envelope:

- A fenced Python block with real control flow
- A 10+ line Bash block that parses and chains tools
- Prose that says "run X, store it, parse it, then feed it to Y"
- Inline `python -c` or heredoc glue shaping structured data
