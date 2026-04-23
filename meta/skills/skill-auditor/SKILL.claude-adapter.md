---
harness: claude
skill: skill-auditor
---

# Skill Auditor — Claude Harness Adapter

This file supplements `SKILL.md` with Claude-specific paths.
A Codex user does NOT need to read this file.

## Standards File Paths (Claude)

```
quality_standard="~/.claude/standards/skills/quality.md"
tier_standard="~/.claude/standards/skills/token-budget-tiers.md"
```

Load both before auditing or rewriting any skill.

## Skills Directory (Claude)

The skills directory for subagent benchmark prompts is `~/.claude/skills/`:

```
Load skill: ~/.claude/skills/{skill-name}/SKILL.md
```

## Eval Viewer Script (Claude)

```
malte/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/eval-viewer/generate_review.py
```

Usage:
```bash
python <eval-viewer-path> workspace/{skill-name} --skill-name {skill-name}
```

## Fleet Audit Dispatch (Claude)

Claude dispatches the full fleet audit to the dedicated subagent:

```python
Agent(subagent_type='meta:skill-auditor', prompt=$ARGUMENTS)
```

The subagent runs on Opus with an isolated context window.
