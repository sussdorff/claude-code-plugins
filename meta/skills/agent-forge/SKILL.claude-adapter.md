---
harness: claude
skill: agent-forge
---

# Agent Forge — Claude Harness Adapter

This file supplements `SKILL.md` with Claude-specific notes.
A Codex user does NOT need to read this file.

## No Claude-Specific Adaptations Required

`agent-forge` contains no harness-specific MCP tool calls or slash-command syntax.
References to `.claude/agents/` in the skill are structural documentation about
agent storage locations (relative paths), not harness-home paths.

## Storage Locations (Claude)

In Claude Code, the agent storage locations are:
- Project-level: `.claude/agents/` (checked into git, highest priority)
- User-level: `~/.claude/agents/` (personal use)
- Plugin: `agents/` directory in plugin structure

The `disableModelInvocation: true` frontmatter key in the skill's YAML is a Claude Code
runtime flag that prevents auto-delegation to this skill. It must stay in `SKILL.md`.
