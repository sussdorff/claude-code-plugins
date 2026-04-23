# Bead Orchestrator Library

Python package for bead-orchestrator and wave-orchestrator workflow logic. This is the **canonical home** for deterministic orchestrator code — claim/parse/aggregate/route/gate operations and cost metrics.

If you find yourself tempted to put workflow logic into a skill body, an agent `.md`, or a shell one-liner embedded in prose: stop and add a module here instead. See `meta/skills/skill-auditor/references/skill-script-first.md`.

## Modules

| Module | Purpose |
|--------|---------|
| `metrics.py` | SQLite persistence for per-bead token-cost tracking. Schema, writes, queries. |
| `routing.py` | Bead-orchestrator routing (which phase/agent handles what). |
| `gate.py` | Plan Review Gate — enforces plan approval before implementation starts. |
| `parse_debrief.py` | Parses subagent debrief sections out of message text. |
| `aggregate_debriefs.py` | Merges multiple parsed debrief dicts into one aggregate. |
| `ingest_ccusage.py` | Imports Claude Code token/cost data from `ccusage` into `metrics.db`. |
| `ingest_codex.py` | Imports Codex CLI token/cost data from `@ccusage/codex` into `metrics.db`. |
| `backfill_codex.py` | Retroactively backfills Codex token+cost data into `metrics.db`. |

## Design Pattern

**Module + thin CLI wrapper.** Orchestrator logic lives here as an importable Python module. If a caller needs a shell entry point, add a thin wrapper under `beads-workflow/scripts/` that imports the module and calls `main()`.

Example: `beads-workflow/scripts/wave-poll.py` is the reference implementation — it imports shared helpers and emits the canonical `execution-result` envelope (see `core/contracts/README.md`).

## Output Contract

Scripts wrapping these modules follow the `execution-result` envelope contract when returning multi-field data. Bare stdout is only allowed for single atomic values (UUID, path, count).

See `core/contracts/execution-result.schema.json` and `meta/skills/agent-forge/references/execution-result-contract.md` for the rule and Python emit pattern.

## Tests

Module-level tests live in `tests/` (pytest). Run:

```bash
cd beads-workflow/lib/orchestrator
python3 -m pytest tests/
```

Script-level (integration) tests for wrappers live in `beads-workflow/scripts/tests/`.

## Adding a New Module

1. Drop `<name>.py` here with a one-line module docstring (first line matters — it appears in the table above and in tooling that auto-generates indexes).
2. Add tests under `tests/`.
3. If you need a CLI entry point, add `beads-workflow/scripts/<name>.py` (≈5 lines: import module, call `main()`, exit).
4. If the wrapper returns multi-field data, emit `execution-result` — do **not** invent ad-hoc JSON shapes.
5. Update the table above.

## What Does NOT Belong Here

- User-facing agent prompts (`*.md`) — those live in `beads-workflow/agents/` or skill directories
- Shell-only wrappers — those live in `beads-workflow/scripts/`
- One-off throwaway scripts — if it's truly single-use, keep it in `scripts/` with a `# one-shot:` comment; if it's reusable, promote it to a module here
