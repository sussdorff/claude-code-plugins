---
harness: claude
skill: token-cost
---

# Token Cost — Claude Harness Adapter

This file supplements `SKILL.md` with Claude-specific paths and tools.
A Codex user does NOT need to read this file.

## Script Invocation (Claude)

```bash
~/.claude/skills/token-cost/scripts/measure-context.sh [OPTIONS]
```

Default scans: `~/.claude/skills/`, `~/.claude/agents/`, `~/.claude/CLAUDE.md`, `~/.claude/settings.json`

## Save Observation (Claude)

When the script outputs a `### SAVE_OBSERVATION` block, call:

```
mcp__open-brain__save_memory(
  type="observation",
  title="<title from output>",
  text="<full text block>"
)
```

If the open-brain MCP server is unavailable, skip this step.

## Standards Paths (Claude)

- Token budget tiers: `~/.claude/standards/skills/token-budget-tiers.md`
- Skill auditor: `~/.claude/skills/skill-auditor/SKILL.md`
