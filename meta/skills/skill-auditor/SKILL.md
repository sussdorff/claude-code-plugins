---
name: skill-auditor
model: sonnet
description: Audit and score agent skills fleet-wide; validate or check a single skill for EXTRACTABLE_CODE; improve weak skills surgically. Triggers on audit skills, skill health check, fleet quality, improve skill, fix skill, rewrite skill, validate skill, check skill, skill creation.
---

# Skill Auditor

Dispatches to the dedicated Opus subagent for all audit and improve work.
For single-skill validation, run `validate-skill.py` directly (no subagent needed).

## When to Use

- "Audit all skills" / "skill health check" / "fleet quality report"
- "How good are my skills?" / "score all skills" / "which skills need work?"
- "improve skill X" / "fix weak skill" / "rewrite {skill-name}"
- "validate skill X" / "check skill X" / "does this skill have extractable code?"
- During skill creation to verify the new SKILL.md is clean

## Validate Single Skill

For a fast, focused check of one skill without a full fleet audit, run the standalone
validator directly:

```bash
python3 meta/skills/skill-auditor/scripts/validate-skill.py <skill-dir>
python3 meta/skills/skill-auditor/scripts/validate-skill.py <skill-dir> --strict
```

Exit 0 = clean. Exit 1 = blocking finding (or any finding in `--strict` mode).
Exit 2 = file not found / parse error.

See `references/skill-script-first.md` for the full script-first authoring rule,
allowed exceptions, and when to use JSON vs bare value output contracts.

## Fleet Audit Dispatch

```python
Agent(subagent_type='meta:skill-auditor', prompt=$ARGUMENTS)
```

All audit logic, scoring dimensions, tier budgets, grade thresholds, improve-mode workflow,
and eval-viewer integration live in the subagent at `meta/agents/skill-auditor.md`.

The subagent runs on Opus for deterministic reasoning quality and an isolated context window.
