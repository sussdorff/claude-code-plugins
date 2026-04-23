# Script-First Rule

> **Scope**: claude-code-plugins — applies to all SKILL.md, agent `.md`, and helper script authoring.

Executable workflow logic lives in `scripts/` (preferably Python) or in a Python module under `beads-workflow/lib/orchestrator/`. Skill bodies and agent `.md` files are **system prompts**, not executable notebooks.

Python is the default script language; Bash is permitted only by exception — see `dev-tools/python-default-bash-exception`.

## BLOCKING violations

- Fenced `bash`/`sh`/`zsh` block with **>5 real lines** (comments/blank excluded) in a SKILL.md or agent body
- Fenced `python` block with **>3 real lines** in a SKILL.md or agent body
- Inline `python -c "..."` or `uv run python -c "..."` anywhere in a skill/agent body

## ADVISORY violations

- Shell block with 3+ pipeline markers (`|`, `$(`, `grep`/`jq`/`sed`/`awk`/`sqlite3`, `2>&1`) — even on a single line
- Ordered list with 4+ steps where each item contains a tool/action keyword (`run`, `parse`, `grep`, `query`, `call`, …) — this is the prose equivalent of embedded code

## Allowed

- Single-command examples (≤1 real line, no pipeline markers) as usage illustrations
- Snippets in files under a skill's `references/` directory (reference docs, not active body)
- Comments (lines starting with `#`) — not counted toward thresholds

## Enforcement

Run before every skill/agent commit:

```bash
python3 meta/skills/skill-auditor/scripts/validate-skill.py <skill-dir>
# --strict: advisory findings also fail
```

Exit 0 = clean. Exit 1 = BLOCKING finding. Exit 2 = parse error.

## Canonical Extraction Targets

| Logic type | Extract to |
|------------|-----------|
| Orchestrator / workflow / metrics / parsing | `beads-workflow/lib/orchestrator/` (Python module) + thin wrapper in `beads-workflow/scripts/` |
| Generic shell helper | `scripts/` sibling to the skill/agent |
| Multi-field structured output | emit `core/contracts/execution-result.schema.json` — see `dev-tools/execution-result-envelope` standard |

## Full Authoring Reference

`meta/skills/skill-auditor/references/skill-script-first.md` — complete rule definition, allowed exceptions, validator behavior, wiring into skill-creation checklist.

## Why

Skills are loaded into every agent invocation as context tokens. Inline code bloats the prompt, degrades token efficiency, and blurs the line between *what the agent must decide* (prompt responsibility) and *what deterministic code already does* (script responsibility). Extracted scripts are testable, versionable, and replaceable without re-reading the prompt.
