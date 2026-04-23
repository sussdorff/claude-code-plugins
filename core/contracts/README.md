# Core Contracts

Cross-script JSON schemas that define how agent-facing helpers communicate with their callers. Treat these as stable interface contracts — scripts emit them, agents consume them, tests validate them.

## What Lives Here

| File | Purpose | Used By |
|------|---------|---------|
| `execution-result.schema.json` | Canonical multi-field result envelope for helper scripts. Fields: `status` (ok/warning/error), `summary`, `data`, `errors`, `next_steps`, `open_items`, `meta`. | All helper scripts that return more than one field or need to signal partial/degraded outcomes |

## When to Emit `execution-result`

| Output shape | Use |
|--------------|-----|
| Single atomic value (a UUID, a path, a count, a boolean) | Bare stdout |
| Multiple fields, degraded modes, structured errors, next-step guidance | `execution-result.schema.json` envelope |

A helper that prints bare values forces the caller to write "run, check, reparse" prose. The envelope moves that branching signal into `status` and `data`, so the caller makes decisions on structured fields — not text.

## Exit-Code Convention

- **Exit 0** when the script emitted a valid envelope, even if `status` is `warning` or `error`
- **Exit non-zero** only when the helper could not honor the contract at all (crash, malformed invocation, schema violation)

Branching belongs in JSON, not in shell error handling.

## Authoring References

- **Contract spec** — `meta/skills/agent-forge/references/execution-result-contract.md` (field semantics, Python emit pattern, worked example)
- **Script-first rule** — `meta/skills/skill-auditor/references/skill-script-first.md` (when to extract logic out of skill/agent bodies into scripts that emit this envelope)

## Reference Implementation

`beads-workflow/scripts/wave-poll.py` — emits `execution-result` for wave-completion polling. Copy this shape when writing a new helper.

## Validation

The schema is draft-07 JSON Schema. Tests that validate emitted envelopes live in:

- `tests/test_skill_auditor_validate_skill.py`
- `tests/test_agent_forge_validate_agent.py`
- `beads-workflow/scripts/tests/test_wave_poll.py`

## Adding a New Contract

1. Drop the schema file here as `<name>.schema.json` (draft-07).
2. Add a row to the table above.
3. Link the authoring reference (or add one to `meta/skills/.../references/`).
4. Add tests that validate at least one real producer against the schema.
5. Update this README.

Do **not** duplicate a schema inline in a skill or agent body — reference the file path instead.
