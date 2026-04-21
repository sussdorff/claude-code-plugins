---
harness: claude
skill: agent-forge
---

# Agent Forge — Claude Harness Adapter

This file supplements `SKILL.md` with Claude Code-specific mechanics.
A Codex user does NOT need to read this file.

## Storage Locations (Claude Code)

In Claude Code, the agent storage locations (highest to lowest priority) are:
- Project-level: `.claude/agents/` (checked into git, highest priority)
- CLI-defined: `--agents` flag
- User-level: `~/.claude/agents/` (personal use)
- Plugin: `agents/` directory in plugin structure

When initializing a new agent file, use:
```bash
python3 scripts/init-agent.py <agent-name> --path .claude/agents/
```

When validating an agent:
```bash
python3 scripts/validate-agent.py .claude/agents/<agent-name>.md
```

## Agent File Format (Claude Code)

Claude Code uses a single `.md` file with YAML frontmatter — this is the supported format.
The split format (agent.yml + prompt.md) is documented in references but the single-file
format is what Claude Code loads from `.claude/agents/`.

## Frontmatter Note

The `disableModelInvocation: true` frontmatter key in the skill's YAML is a Claude Code
runtime flag that prevents auto-delegation to this skill. It must stay in `SKILL.md`.
