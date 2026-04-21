---
name: skill-auditor
model: sonnet
description: Audit and score agent skills fleet-wide; improve weak skills surgically. Triggers on audit skills, skill health check, fleet quality, improve skill, fix skill, rewrite skill.
---

# Skill Auditor

Dispatches to the dedicated Opus subagent for all audit and improve work.

## When to Use

- "Audit all skills" / "skill health check" / "fleet quality report"
- "How good are my skills?" / "score all skills" / "which skills need work?"
- "improve skill X" / "fix weak skill" / "rewrite {skill-name}"

## Dispatch

```python
Agent(subagent_type='meta:skill-auditor', prompt=$ARGUMENTS)
```

All audit logic, scoring dimensions, tier budgets, grade thresholds, improve-mode workflow,
and eval-viewer integration live in the subagent at `meta/agents/skill-auditor.md`.

The subagent runs on Opus for deterministic reasoning quality and an isolated context window.
